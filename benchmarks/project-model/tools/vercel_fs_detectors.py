"""@vercel/fs-detectors 7.12.1 with @vercel/frameworks 3.35.0: framework, workspaces, monorepo manager, package manager.

A small Node script (below) opens the fixture with the package's own `LocalFileSystemDetector` and calls
`getWorkspaces`, `getWorkspacePackagePaths`, `detectFrameworks` (every framework of the catalogue that matches a
directory), `detectFramework` with `packageManagers` and `monorepoManagers`. Frameworks are looked for at the root
and in every workspace member, since the package does not walk a monorepo by itself. Normalisation: the catalogue
also holds runtimes and deployment kinds (RUNTIMES: node, python, go, ruby, rust, bun, container, services, null),
which are not frameworks and go to `detail` only; the unit of a JavaScript framework is the `name` of the
package.json of its directory (read from the fixture); the evidence is the first detector of the framework whose
file exists and whose pattern matches (computed by the script, the package returns none). `autoDetectServices`
returns Vercel deployment services, not external ones, and is not mapped.
"""
from __future__ import annotations

import json
from pathlib import Path

import _fw

VERSION = "7.12.1 (@vercel/frameworks 3.35.0)"
RUNTIMES = {"node", "python", "go", "ruby", "rust", "bun", "container", "services", "null", "deno"}
SCRIPT = r"""
const path = require('path');
const NM = process.env.PM_NODE_MODULES || '/opt/tools/node_modules';
const fsd = require(NM + '/@vercel/fs-detectors');
const { frameworks } = require(NM + '/@vercel/frameworks');
const root = path.resolve(process.argv[2]);
const rel = (p) => path.posix.normalize(p.replace(/^\/+/, '') || '.');
async function evidence(fs, f) {
  const d = f.detectors || {};
  for (const group of [d.every || [], d.some || []]) {
    for (const x of group) {
      if (x.matchPackage) { if (await fs.hasPath('package.json')) return 'package.json'; continue; }
      if (!x.path || !(await fs.hasPath(x.path))) continue;
      if (x.matchContent) {
        const text = (await fs.readFile(x.path)).toString();
        if (!new RegExp(x.matchContent).test(text)) continue;
      }
      return x.path;
    }
  }
  return null;
}
(async () => {
  const fs = new fsd.LocalFileSystemDetector(root);
  const out = { workspaces: [], projects: [] };
  out.workspaces = await fsd.getWorkspaces({ fs });
  for (const w of out.workspaces) w.paths = await fsd.getWorkspacePackagePaths({ fs, workspace: w });
  out.packageManager = await fsd.detectFramework({ fs, frameworkList: fsd.packageManagers });
  out.monorepoManager = await fsd.detectFramework({ fs, frameworkList: fsd.monorepoManagers });
  const dirs = new Set(['.']);
  for (const w of out.workspaces) for (const p of w.paths) dirs.add(rel(path.posix.join(w.rootPath, p)));
  for (const dir of dirs) {
    const sub = new fsd.LocalFileSystemDetector(path.join(root, dir));
    const found = [];
    for (const f of await fsd.detectFrameworks({ fs: sub, frameworkList: frameworks })) {
      found.push({ slug: f.slug, name: f.name, version: fsd.detectFrameworkVersion(f) || null,
                   evidence: await evidence(sub, f) });
    }
    out.projects.push({ dir, frameworks: found });
  }
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(e.stack); process.exit(1); });
"""


def normalise(raw: dict, fixture: Path) -> dict:
    frameworks, ignored = [], []
    for project in raw["projects"]:
        unit = _fw.package_name(fixture, project["dir"])
        for item in project["frameworks"]:
            if item["slug"] in RUNTIMES:
                ignored.append({"slug": item["slug"], "dir": project["dir"]})
                continue
            evidence = item.get("evidence")
            frameworks.append({"name": item["name"], **({"unit": unit} if unit else {}),
                               **({"evidence": _fw.posix(f"{project['dir']}/{evidence}")} if evidence else {})})
    out = {"frameworks": frameworks, "services": [],
           "detail": {"packageManager": raw["packageManager"], "monorepoManager": raw["monorepoManager"],
                      "workspaces": raw["workspaces"], "not_frameworks": ignored,
                      "versions": {f"{p['dir']}:{i['slug']}": i["version"] for p in raw["projects"]
                                   for i in p["frameworks"] if i["version"]}}}
    if raw["workspaces"]:
        out["workspace"] = [{"tool": w["type"], "root": _fw.posix(w["rootPath"]),
                             "members": [_fw.posix(m) for m in w["paths"]]} for w in raw["workspaces"]]
        if len(out["workspace"]) == 1:
            out["workspace"] = out["workspace"][0]
    else:
        out["workspace"] = None
    return out


def run(fixture_dir, work_dir) -> dict:
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    script = work / "vercel_detect.cjs"
    script.write_text(SCRIPT, encoding="utf-8")
    code, out, err = _fw.execute(["node", script, Path(fixture_dir).resolve()], work)
    if code != 0:
        raise RuntimeError(f"fs-detectors script exited {code}: {(err or out)[-400:]}")
    return normalise(json.loads(out.strip().splitlines()[-1]), Path(fixture_dir))
