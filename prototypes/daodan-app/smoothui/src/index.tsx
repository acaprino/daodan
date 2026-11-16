import React from "react";
import { createRoot, type Root } from "react-dom/client";
import AITaskList, { type AITask } from "./ai-task-list";
import AnimatedStepper from "./animated-stepper";

type AppState = {
  progress: number;
  runStatus: string;
  reviewStep: number;
};

const roots = new Map<HTMLElement, Root>();

function renderAt(id: string, component: React.ReactNode) {
  const host = document.getElementById(id);
  if (!host) return;
  let root = roots.get(host);
  if (!root) {
    root = createRoot(host);
    roots.set(host, root);
  }
  root.render(component);
}

function phaseStatus(state: AppState, start: number, end: number) {
  if (state.progress >= end) return "done";
  if (state.progress < start) return "pending";
  if (state.runStatus === "error") return "failed";
  return state.runStatus === "running" ? "running" : "pending";
}

function Pipeline({ state }: { state: AppState }) {
  const currentNote = state.runStatus === "paused" ? "In pausa · demo" : state.runStatus === "error" ? "Interrotta · demo" : "In corso · demo";
  const tasks: AITask[] = [
    { id: "scan", label: "Scan · inventario e pre-mappa", status: phaseStatus(state, 0, 20), note: state.progress >= 20 ? "Completata · demo" : state.runStatus === "idle" ? "In attesa" : currentNote },
    { id: "analyze", label: "Analyze · analyzer per tecnologia", status: phaseStatus(state, 20, 65), note: state.progress >= 65 ? "Completata · demo" : state.progress >= 20 ? currentNote : "In attesa" },
    { id: "dynamic", label: "Dynamic · osservazione dei test", status: phaseStatus(state, 65, 75), note: state.progress >= 65 ? "Esclusa dalla demo" : "Prevista · esclusa dalla demo" },
    { id: "union", label: "Union · collegamento dei grafi", status: phaseStatus(state, 75, 100), note: state.progress >= 100 ? "Completata · demo" : state.progress >= 75 ? currentNote : "In attesa" },
  ];
  return <div className="daodan-pipeline"><AITaskList className="smooth-tasks" label="Scan → Analyze → Dynamic → Union" tasks={tasks} /><div className="dynamic-proposal"><span className="dynamic-proposal-mark">↳</span><div><strong>Dynamic è implementato nel prodotto.</strong><span>Escluso solo da questa demo</span><p>Questa simulazione non avvia test o container. La sintesi semantica si legge dopo l’unione del grafo.</p></div></div></div>;
}

function ReviewStages({ currentStep }: { currentStep: number }) {
  const steps = [
    { label: "Perimetro", description: "Candidato e chiamante", content: <div className="smooth-stage-content"><strong>Un cambiamento, un percorso da seguire.</strong><p>La review storica confronta <code>109c1d7</code> con la base <code>2889c58</code>. Il chiamante trovato è <code>OrderService.checkout</code> in <code>service.py:26</code>. Il pacchetto di impatto non era disponibile.</p></div> },
    { label: "Analisi", description: "Auditor selezionato", content: <div className="smooth-stage-content"><strong>La regola di prezzo è rimasta invariata.</strong><p>L’auditor <code>local-correctness</code> confronta la docstring con le due sottrazioni di <code>compute_discount</code>. I test verdi non verificavano il totale numerico.</p></div> },
    { label: "Verifica", description: "Premessa ed effetto", content: <div className="smooth-stage-content"><strong>Premessa HOLDS. Correttezza REAL.</strong><p>La verifica riproduce 97,60 € invece di 109,80 € per 100 € con sconto 10%. Confidenza 98, evidenza <code>reproduced</code>. La base supera la stessa verifica.</p></div> },
    { label: "Consolidamento", description: "Finding e lacune", content: <div className="smooth-stage-content"><strong>Un finding mantenuto, con i suoi limiti.</strong><p>Il report conserva la correzione proposta e quattro lacune esplicite. Puoi accettare o rifiutare il fix e preparare la risposta. Il checkout attuale contiene già un solo sconto.</p></div> },
  ];
  return <AnimatedStepper className="smooth-review" currentStep={currentStep} steps={steps} allowClickNavigation onStepChange={step => window.dispatchEvent(new CustomEvent("daodan:review-step", { detail: step }))} />;
}

const bridge = {
  mount(state: AppState) {
    renderAt("smooth-analysis-tasks", <Pipeline state={state} />);
    renderAt("smooth-review-stages", <ReviewStages currentStep={Math.max(0, Math.min(3, state.reviewStep ?? 3))} />);
  },
  dispose() {
    for (const root of roots.values()) root.unmount();
    roots.clear();
  },
};

(window as unknown as { DaodanSmoothUI: typeof bridge }).DaodanSmoothUI = bridge;
