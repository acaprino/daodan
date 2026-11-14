import { Chart } from 'chart.js';

export function draw(canvas, values) {
  return new Chart(canvas, { type: 'line', data: { datasets: [{ data: values }] } });
}
