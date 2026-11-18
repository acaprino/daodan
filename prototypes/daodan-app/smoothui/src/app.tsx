// The bridge of the app's page (plugins/codebase-map/assets/app): AITaskList over the run's steps. The page passes
// every task with its state and note; nothing here decides one.
import { createRoot, type Root } from "react-dom/client";
import AITaskList, { type AITask } from "./ai-task-list";

let mounted: { host: HTMLElement; root: Root } | null = null;

const bridge = {
  /** Renders the tasks in `host`; the same host keeps its root, so a row that changes state animates. */
  mount(host: HTMLElement, label: string, tasks: AITask[]) {
    if (mounted?.host !== host) {
      bridge.unmount();
      mounted = { host, root: createRoot(host) };
    }
    mounted.root.render(<AITaskList className="smooth-tasks" label={label} tasks={tasks} />);
  },
  /** Before the page replaces the markup that holds the host. */
  unmount() {
    mounted?.root.unmount();
    mounted = null;
  },
};

(window as unknown as { DaodanSmoothUI: typeof bridge }).DaodanSmoothUI = bridge;
