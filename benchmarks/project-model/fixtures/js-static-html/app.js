import { createApp } from "vue";

createApp({ template: "<p>hi</p>" }).mount("#app");
new Chart(document.getElementById("chart"), { type: "bar", data: { labels: [], datasets: [] } });
