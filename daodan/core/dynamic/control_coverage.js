// Injected at document creation in the container. DOM identity, values and URL stay
// in this document. The runner receives only local numeric IDs and two event names.
(() => {
  "use strict";
  if (window !== window.top || window.__daodanControls) return;

  const roles = ["button", "link", "tab", "menuitem", "checkbox", "radio", "switch"];
  const selector = ["button", "a[href]", "input:not([type=hidden i])", "select", "textarea",
    "summary", ...roles.map(role => `[role="${role}" i]`)].join(",");
  const ids = new WeakMap();
  const observed = new Map();
  const rowLimit = 4096;
  let dropped = false;
  let nextId = 0;
  let state = 1;
  let url = location.href;
  let previousFields;
  let gesture;

  function invalidate() {
    state++;
    gesture = undefined;
    previousFields = undefined;
  }

  const mutations = new MutationObserver(invalidate);
  mutations.observe(document, { subtree: true, childList: true, attributes: true, characterData: true });

  function syncDocument() {
    if (mutations.takeRecords().length || location.href !== url) {
      url = location.href;
      invalidate();
    }
  }

  // Assignments to form properties need not fire events or mutate an attribute.
  // Compare their live values only when consulting or collecting evidence.
  function syncFields() {
    const fields = [document.activeElement];
    for (const el of document.querySelectorAll("input,select,textarea")) {
      fields.push(el, el.value);
      if (el.localName === "input") {
        fields.push(el.checked, el.indeterminate);
        if (el.type === "file") fields.push(...el.files);
      } else if (el.localName === "select" && el.multiple) {
        fields.push(...el.selectedOptions);
      }
    }
    if (previousFields && (fields.length !== previousFields.length ||
        fields.some((value, i) => value !== previousFields[i]))) invalidate();
    previousFields = fields;
  }

  function eventFor(el) {
    if (!(el instanceof Element) || el.getRootNode() !== document || !el.matches(selector) ||
        el.matches(":disabled") || el.closest("[hidden],[inert],[aria-disabled=true i]")) return;
    if (el.checkVisibility && !el.checkVisibility({ visibilityProperty: true })) return;
    if (el.localName === "select" || el.localName === "textarea") return "change";
    if (el.localName === "input" && !["button", "submit", "reset", "image"].includes(el.type)) return "change";
    return "click";
  }

  function eventControl(e) {
    const path = e.composedPath();
    if (path.some(node => node instanceof ShadowRoot)) return;
    const controls = path.filter(node => node instanceof Element && node.matches(selector));
    if (controls.length === 1 && eventFor(controls[0])) return controls[0];
  }

  function id(el) {
    if (!ids.has(el)) ids.set(el, ++nextId);
    return ids.get(el);
  }

  const key = (control, event, at) => `${control}:${event}:${at}`;

  function record(el, event, at) {
    const control = id(el);
    const signature = key(control, event, at);
    if (observed.has(signature)) return;
    if (observed.size === rowLimit) { dropped = true; return; }
    observed.set(signature, { control, event, state: at });
  }

  const listen = (type, fn) => window.addEventListener(type, fn, { capture: true, passive: true });
  // pagehide publishes the last state a user could interact with. A restored page gets a new state on pageshow.
  for (const type of ["hashchange", "popstate", "pageshow", "reset", "resize"]) {
    listen(type, invalidate);
  }
  listen("visibilitychange", () => { if (document.visibilityState === "visible") invalidate(); });
  window.navigation?.addEventListener("currententrychange", invalidate);

  for (const type of ["pointerdown", "keydown"]) listen(type, e => {
    syncDocument();
    const el = e.isTrusted && eventControl(e);
    gesture = undefined;
    if (el && eventFor(el) === "change") {
      syncFields();
      gesture = { el, state };
    }
  });
  listen("focusin", e => {
    // A pointer can focus its control before the browser changes its value.
    const started = gesture;
    invalidate();
    if (e.isTrusted && started && started.el === e.target) gesture = { el: e.target, state };
  });
  listen("pointercancel", () => { gesture = undefined; });
  listen("click", e => {
    syncDocument();
    const el = e.isTrusted && eventControl(e);
    if (el && eventFor(el) === "click" && e.button === 0 &&
        !e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey) {
      syncFields();
      record(el, "click", state);
    }
    if (gesture && el !== gesture.el) gesture = undefined;
  });
  listen("input", e => {
    syncDocument();
    const started = gesture;
    invalidate();
    if (e.isTrusted && started && !started.inputSeen && started.el === e.target) {
      gesture = { ...started, inputSeen: true };
    }
  });
  listen("change", e => {
    syncDocument();
    const el = e.isTrusted && eventControl(e);
    // change arrives after the default action (a checkbox is already toggled).
    // Only the matched gesture before that transition supplies a source state.
    if (el && gesture?.el === el && gesture.inputSeen && eventFor(el) === "change") {
      record(el, "change", gesture.state);
    }
    invalidate();
  });

  function shouldExploreAt(el, event) {
    if (!event || eventFor(el) !== event) return true;
    return !observed.has(key(id(el), event, state));
  }

  Object.defineProperty(window, "__daodanControls", { value: Object.freeze({
    shouldExplore(el, event) {
      syncDocument();
      syncFields();
      return shouldExploreAt(el, event);
    },
    report() {
      syncDocument();
      syncFields();
      const pending = [];
      let clipped = dropped;
      for (const el of document.querySelectorAll(selector)) {
        const event = eventFor(el);
        if (event && shouldExploreAt(el, event)) {
          if (pending.length === rowLimit) { clipped = true; break; }
          pending.push({ control: id(el), event, state });
        }
      }
      return { observed: Array.from(observed.values(), row => ({ ...row })), pending,
        ...(clipped && {truncated: true}) };
    }
  }) });
})();
