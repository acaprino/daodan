// React 19. Requirement: editing a draft survives unrelated clock updates.
import {useState} from "react";
export function Screen() {
  const [tick, setTick] = useState(0);
  function Draft() {
    const [text, setText] = useState("");
    return <input value={text} onChange={e => setText(e.target.value)} />;
  }
  return <><button onClick={() => setTick(tick + 1)}>Tick {tick}</button><Draft /></>;
}
