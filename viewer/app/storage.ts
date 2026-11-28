// Where the person was looking: all the browser keeps. The server's state is the truth.
import type { Host } from './server.ts';

export const STORAGE = 'daodan-app-v3';  // v3: the step of the analysis is an id of the plan, which the stages of v2 are not
export type Place = 'analysis' | 'graph' | 'engine';
// The step of the analysis in view: «repository», or the id of a step of the plan (`pipeline.IDS`).
export type Stage = string;
export type Kept = {
  screen: Place; analysisStage: Stage; repositoryUrl: string; runId: string;
  treeMode: 'directories' | 'units'; treeSearch: string; treeSelected: string; treeOpen: Record<string, boolean>;
  graphSearch: string; graphRoot: string; graphOpen: string[];
  graphDirection: 'out' | 'in' | 'both'; graphDepth: '1' | '2' | 'all'; graphKind: 'all' | 'calls' | 'imports' | 'uses';
};

const PLACES: readonly string[] = ['analysis', 'graph', 'engine'];
export const DEFAULTS: Kept = {
  screen: 'analysis', analysisStage: 'repository', repositoryUrl: '', runId: '',
  treeMode: 'directories', treeSearch: '', treeSelected: '', treeOpen: {},
  graphSearch: '', graphRoot: '', graphOpen: [], graphDirection: 'both', graphDepth: 'all', graphKind: 'all',
};

// What was kept, and whether the storage could be read.
export function readKept(storage: Host['storage']): { kept: Kept; available: boolean } {
  let kept = { ...DEFAULTS }, available = true;
  try {
    const stored = JSON.parse(storage().getItem(STORAGE) || 'null');
    if (stored && typeof stored === 'object') kept = { ...DEFAULTS, ...stored };
  } catch { available = false; }
  if (!PLACES.includes(kept.screen)) kept.screen = 'analysis';
  if (typeof kept.analysisStage !== 'string' || !kept.analysisStage) kept.analysisStage = 'repository';
  if (!Array.isArray(kept.graphOpen) || kept.graphOpen.some(id => typeof id !== 'string')) kept.graphOpen = [];
  return { kept, available };
}
