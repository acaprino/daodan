/**
 * Office HTML to PPTX entry.
 *
 * Office-owned wrapper around the vendored open-slide exporter. It selects the
 * designed slide panels, enforces the fixed 1920x1080 canvas contract and
 * returns the packaged PPTX bytes as base64. The modules under `../src/lib` are
 * unmodified upstream files; see `UPSTREAM.md` for the pin and the notices.
 */
import { measurePage } from '../src/lib/pptx/measure';
import { ImageStore } from '../src/lib/pptx/images';
import { Rasterizer } from '../src/lib/pptx/raster';
import { createColorNormalizer } from '../src/lib/pptx/color';
import { buildPptxFiles } from '../src/lib/pptx/ooxml';
import { zipSync } from 'fflate';

const PANEL_SELECTOR = '[data-office-slide]';
const NOTES_ATTRIBUTE = 'data-office-notes';
const CANVAS_WIDTH = 1920;
const CANVAS_HEIGHT = 1080;
const GEOMETRY_TOLERANCE_PX = 0.5;
const BASE64_CHUNK = 0x8000;

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
  const problems = contractProblems(panels);
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

  const files = buildPptxFiles({ slides, images: images.images });
  const bytes = zipSync(files);
  return {
    base64: base64FromBytes(bytes),
    panels: panels.length,
    parts: Object.keys(files).sort(),
    scene: summarize(slides),
    images: images.images.map((image) => ({
      id: image.id,
      format: image.format,
      bytes: image.bytes.length,
      svg: image.svg ? image.svg.length : 0,
    })),
  };
}

(window as unknown as { officeHtmlToPptx: typeof convert }).officeHtmlToPptx = convert;
