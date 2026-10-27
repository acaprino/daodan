/**
 * Office HTML to PPTX entry.
 *
 * Office-owned wrapper around the vendored open-slide exporter. It selects the
 * designed slide panels, settles their animations and readiness targets,
 * enforces the fixed 1920x1080 canvas contract and returns the packaged PPTX
 * bytes as base64. The modules under `../src/lib` are unmodified upstream
 * files; see `UPSTREAM.md` for the pin and the notices.
 */
import { measurePage } from '../src/lib/pptx/measure';
import { ImageStore } from '../src/lib/pptx/images';
import { Rasterizer } from '../src/lib/pptx/raster';
import { createColorNormalizer } from '../src/lib/pptx/color';
import { buildPptxFiles } from '../src/lib/pptx/ooxml';
import { zipSync } from 'fflate';

const PANEL_SELECTOR = '[data-office-slide]';
const NOTES_ATTRIBUTE = 'data-office-notes';
const WAITFOR_ATTRIBUTE = 'data-waitfor';
const CANVAS_WIDTH = 1920;
const CANVAS_HEIGHT = 1080;
const GEOMETRY_TOLERANCE_PX = 0.5;
const BASE64_CHUNK = 0x8000;
const SETTLE_TIMEOUT_MS = 15_000;
const WAITFOR_TIMEOUT_MS = 10_000;
const POLL_INTERVAL_MS = 100;
// A fixed entry date keeps the package bytes reproducible; ZIP dates start in 1980.
const ZIP_MTIME = new Date(1980, 0, 1, 0, 0, 0);

// The excluded upstream mount fast-forwarded every animation to its end frame
// before measuring; without it an entrance animation is captured at opacity 0.
const SETTLE_STYLE = `${PANEL_SELECTOR}, ${PANEL_SELECTOR} *, ${PANEL_SELECTOR} *::before, ${PANEL_SELECTOR} *::after {
  animation-delay: -1s !important;
  animation-duration: 1ms !important;
  animation-iteration-count: 1 !important;
  animation-fill-mode: forwards !important;
  transition: none !important;
}`;

function nextFrame(): Promise<void> {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function unsettled(panels: Element[]): number {
  if (typeof document.getAnimations !== 'function') return 0;
  let count = 0;
  for (const animation of document.getAnimations()) {
    const effect = animation.effect as KeyframeEffect | null;
    const target = effect?.target;
    if (!effect || !target || !panels.some((panel) => panel.contains(target))) continue;
    if (effect.getComputedTiming().iterations === Infinity) continue;
    if (animation.playState !== 'finished') count += 1;
  }
  return count;
}

async function settle(panels: Element[]): Promise<string[]> {
  const style = document.createElement('style');
  style.setAttribute('data-office-settle', '');
  style.textContent = SETTLE_STYLE;
  document.head.appendChild(style);
  // Panels stack below the 1080px viewport; bring each into view so content
  // revealed by an IntersectionObserver or a scroll handler exists when measured.
  for (const panel of panels) {
    panel.scrollIntoView({ block: 'start', inline: 'start' });
    await nextFrame();
    await nextFrame();
  }
  window.scrollTo(0, 0);
  await nextFrame();
  await document.fonts.ready;
  const problems: string[] = [];
  const deadline = performance.now() + SETTLE_TIMEOUT_MS;
  while (unsettled(panels) > 0 && performance.now() < deadline) await sleep(POLL_INTERVAL_MS);
  const remaining = unsettled(panels);
  if (remaining > 0) problems.push(`${remaining} animation(s) did not finish within ${SETTLE_TIMEOUT_MS} ms`);

  const targets = panels.flatMap((panel) => [
    ...(panel.matches(`[${WAITFOR_ATTRIBUTE}]`) ? [panel] : []),
    ...Array.from(panel.querySelectorAll(`[${WAITFOR_ATTRIBUTE}]`)),
  ]);
  const waitDeadline = performance.now() + WAITFOR_TIMEOUT_MS;
  for (const target of targets) {
    const selector = target.getAttribute(WAITFOR_ATTRIBUTE) || '';
    if (selector === '') continue;
    let state: 'waiting' | 'found' | 'invalid' = 'waiting';
    while (state === 'waiting' && performance.now() < waitDeadline) {
      try {
        if (target.querySelector(selector) !== null) state = 'found';
      } catch {
        state = 'invalid';
      }
      if (state === 'waiting') await nextFrame();
    }
    if (state === 'invalid') problems.push(`invalid ${WAITFOR_ATTRIBUTE} selector: ${selector}`);
    if (state === 'waiting') problems.push(`${WAITFOR_ATTRIBUTE} target "${selector}" did not appear`);
  }
  await document.fonts.ready;
  await nextFrame();
  return problems;
}

type SceneSummary = {
  nodes: number;
  kinds: Record<string, number>;
  background: boolean;
  notes: boolean;
};

function base64FromBytes(bytes: Uint8Array): string {
  let text = '';
  for (let index = 0; index < bytes.length; index += BASE64_CHUNK) {
    text += String.fromCharCode(...bytes.subarray(index, index + BASE64_CHUNK));
  }
  return btoa(text);
}

function contractProblems(panels: Element[]): string[] {
  const problems: string[] = [];
  panels.forEach((panel, index) => {
    const rect = panel.getBoundingClientRect();
    const position = getComputedStyle(panel).position;
    const label = `panel ${index + 1}`;
    if (
      Math.abs(rect.width - CANVAS_WIDTH) > GEOMETRY_TOLERANCE_PX ||
      Math.abs(rect.height - CANVAS_HEIGHT) > GEOMETRY_TOLERANCE_PX
    ) {
      problems.push(
        `${label} is ${rect.width.toFixed(1)}x${rect.height.toFixed(1)} CSS px, expected ${CANVAS_WIDTH}x${CANVAS_HEIGHT}`,
      );
    }
    if (position === 'static') {
      problems.push(`${label} has position:static, expected position:relative on the panel itself`);
    }
  });
  return problems;
}

function summarize(slides: { background: unknown; nodes: { kind: string }[]; notes: string | null }[]): SceneSummary[] {
  return slides.map((slide) => {
    const kinds: Record<string, number> = {};
    for (const node of slide.nodes) kinds[node.kind] = (kinds[node.kind] ?? 0) + 1;
    return { nodes: slide.nodes.length, kinds, background: slide.background !== null, notes: slide.notes !== null };
  });
}

async function convert(): Promise<{
  base64: string;
  panels: number;
  parts: string[];
  scene: SceneSummary[];
  images: { id: number; format: string; bytes: number; svg: number }[];
}> {
  const panels = Array.from(document.querySelectorAll(PANEL_SELECTOR));
  if (panels.length === 0) {
    throw new Error(`No ${PANEL_SELECTOR} panel found: the design HTML must mark every slide panel with that attribute`);
  }
  const problems = [...(await settle(panels)), ...contractProblems(panels)];
  if (problems.length > 0) {
    throw new Error(`Office HTML contract violated: ${problems.join('; ')}`);
  }

  const images = new ImageStore();
  const color = createColorNormalizer();
  const slides = [];
  for (const panel of panels) {
    const element = panel as HTMLElement;
    const notes = element.getAttribute(NOTES_ATTRIBUTE);
    slides.push(
      await measurePage({
        frame: element,
        notes: notes && notes.trim() ? notes.trim() : null,
        images,
        color,
        rasterizer: new Rasterizer(element),
      }),
    );
  }

  const scene = summarize(slides);
  const empty = scene.flatMap((slide, index) => (slide.nodes === 0 && !slide.background ? [`panel ${index + 1}`] : []));
  if (empty.length > 0) {
    throw new Error(`Office HTML contract violated: ${empty.join(', ')} measured no visible content`);
  }

  const files = buildPptxFiles({ slides, images: images.images });
  const bytes = zipSync(files, { mtime: ZIP_MTIME });
  return {
    base64: base64FromBytes(bytes),
    panels: panels.length,
    parts: Object.keys(files).sort(),
    scene,
    images: images.images.map((image) => ({
      id: image.id,
      format: image.format,
      bytes: image.bytes.length,
      svg: image.svg ? image.svg.length : 0,
    })),
  };
}

(window as unknown as { officeHtmlToPptx: typeof convert }).officeHtmlToPptx = convert;
