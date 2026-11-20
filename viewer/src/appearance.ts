import '@acaprino/imago/css/imago.css';
import { applyLook } from '@acaprino/imago/shell';

const appearance = () => applyLook(document.documentElement, {
  app: 'daodan', look: 'smooth', theme: 'system', glass: false,
});
appearance();
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', appearance);

export const graphControls = { zoomIn: 'Ingrandisci', zoomOut: 'Riduci', fit: 'Inquadra tutto' };
