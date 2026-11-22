import { invoke } from "@tauri-apps/api/core";

function save() {
  return invoke("persist");
}

function probe() {
  return invoke("only_in_tests");
}

function draft() {
  return invoke("on_idle_builder");
}

export function View() {
  return (
    <div>
      <button onClick={save}>Salva profilo</button>
      <button onClick={probe}>Prova</button>
      <button onClick={draft}>Bozza</button>
    </div>
  );
}
