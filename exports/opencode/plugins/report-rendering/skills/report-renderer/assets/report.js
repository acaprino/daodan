"use strict";
// Controls affect the current page only. Canonical source is never written.
for (const checkbox of document.querySelectorAll(".task-item input[type=checkbox]")) {
  checkbox.checked = checkbox.defaultChecked;
}
for (const block of document.querySelectorAll(".table-block")) {
  const controls = block.querySelector(".table-controls");
  const input = controls.querySelector("input");
  const status = controls.querySelector("output");
  const rows = [...block.querySelectorAll("tbody > tr")].filter(row => !row.hasAttribute("data-overall-row"));
  function filterRows() {
    const query = input.value.toLocaleLowerCase().trim();
    let count = 0;
    for (const row of rows) {
      row.hidden = !row.textContent.toLocaleLowerCase().includes(query);
      if (!row.hidden) count += 1;
    }
    status.textContent = `${count} of ${rows.length} rows shown`;
  }
  controls.hidden = false;
  input.addEventListener("input", filterRows);
  filterRows();
}

for (const block of document.querySelectorAll("[data-scorecard]")) {
  const scoreControls = block.querySelector(".score-controls");
  const status = scoreControls.querySelector("[role=status]");
  const scoreRows = [...block.querySelectorAll("tr[data-score-row]")];
  const weightInputs = [...block.querySelectorAll("input[data-weight]")];
  const overall = [...block.querySelectorAll("[data-overall]")];
  const originalCells = overall.map(cell => [...cell.childNodes].map(node => node.cloneNode(true)));
  const originalWeights = weightInputs.map(input => input.value);
  function recompute() {
    const weights = weightInputs.map(input => Number(input.value));
    const invalid = weightInputs.some((input, index) => input.value.trim() === "" || !Number.isFinite(weights[index]) || weights[index] < 0 || weights[index] > 100);
    for (let index = 0; index < weightInputs.length; index += 1) {
      const input = weightInputs[index];
      const valid = input.value.trim() !== "" && Number.isFinite(weights[index]) && weights[index] >= 0 && weights[index] <= 100;
      input.setAttribute("aria-invalid", String(!valid));
    }
    if (invalid) {
      status.textContent = "Enter weights from 0 through 100. The previous outcomes remain visible.";
      return;
    }
    for (let column = 0; column < overall.length; column += 1) {
      let numerator = 0;
      let denominator = 0;
      const qualifiers = new Set(JSON.parse(overall[column].dataset.qualifiers || "[]"));
      for (let row = 0; row < scoreRows.length; row += 1) {
        const cell = scoreRows[row].querySelectorAll("td")[column + 2];
        for (const qualifier of JSON.parse(cell.dataset.qualifiers || "[]")) qualifiers.add(qualifier);
        if (!cell.hasAttribute("data-score")) continue;
        numerator += Number(cell.dataset.score) * weights[row];
        denominator += weights[row];
      }
      const result = denominator === 0 ? block.dataset.unscored : (numerator / denominator).toFixed(1);
      overall[column].textContent = result + (qualifiers.size ? ` (${[...qualifiers].join("; ")})` : "");
    }
    status.textContent = "Exploratory Overall values updated. The original recommendation and evidence are unchanged.";
  }
  for (const input of weightInputs) {
    input.closest(".weight-editor").hidden = false;
    input.addEventListener("input", recompute);
  }
  scoreControls.hidden = false;
  scoreControls.querySelector("button").addEventListener("click", () => {
    weightInputs.forEach((input, index) => { input.value = originalWeights[index]; input.removeAttribute("aria-invalid"); });
    overall.forEach((cell, index) => cell.replaceChildren(...originalCells[index].map(node => node.cloneNode(true))));
    status.textContent = "Original weights and Overall values restored.";
  });
}
