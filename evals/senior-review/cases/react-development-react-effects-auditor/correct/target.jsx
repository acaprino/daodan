// React 19. Requirement: every pulse displays the current label; globals are browser DOM APIs.
import {useEffect} from "react";
export function Pulse({label}) {
  useEffect(() => {
    const onPulse = () => { document.title = label; };
    window.addEventListener("pulse", onPulse);
    return () => window.removeEventListener("pulse", onPulse);
  }, [label]);
  return null;
}
