const { invoke } = window.__TAURI__.core;

window.addEventListener("DOMContentLoaded", () => {
  const input = document.querySelector("#greet-input");
  const msg = document.querySelector("#greet-msg");
  document.querySelector("#greet-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.textContent = await invoke("greet", { name: input.value });
  });
});
