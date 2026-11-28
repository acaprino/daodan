"""The applications `modal_probe.py` measures: where they are, at which commit, under which licence, and the module that exports the app as
chosen by hand (only to know what `inspectRoutes` would give if the module were known: the decision rule counts the declared one). Nothing of
them is in the repository: each is fetched at its commit while the Modal image is built (`https://codeload.github.com/<repository>/tar.gz/<commit>`)
and read, restored and loaded only there. Licences read from the repository's licence file at that commit (27 November 2026).
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
DOCUMENSO = json.loads((HERE.parents[0] / "project-model/fixtures/real-stack-documenso/source.json").read_text(encoding="utf-8"))

# name -> (repository, commit, licence, modules chosen by hand, note); `fixture` is this folder's own `fixture/`
APPS = {
    "real-stack-documenso": ("documenso/documenso", DOCUMENSO["commit"], DOCUMENSO["licence"], ["apps/remix/server/router.ts"],
                             "npm workspace; the server is Hono with `basePath`, `route` of sub-apps from other packages; the bundle entry is in rollup.config.mjs"),
    "ramen-api": ("yusukebe/ramen-api", "a2d3f10137fdd8a128b61b09e022fa7421bc3bf3", "MIT", ["src/index.ts"],
                  "Cloudflare Workers, pnpm; `main` in package.json and in wrangler.jsonc; a `@/` path alias of tsconfig"),
    "hono-open-api-starter": ("w3cj/hono-open-api-starter", "0d5f3bf523f525667d58edb38011e377e5898fc4", "MIT", ["src/app.ts"],
                              "Node server, pnpm; `OpenAPIHono` routes (`openapi(route, handler)`); no `main`: `dev` runs `tsx watch src/index.ts`"),
    "fixture": (None, None, "MIT (this repository)", ["src/index.js"], "new Hono(), route('/api', sub), basePath, named and inline handlers, middleware"),
}
NOIR = ("https://github.com/owasp-noir/noir/releases/download/v1.5.0/noir-v1.5.0-linux-x86_64",  # `entry_points/noir.py` DOWNLOAD
        "4e176c92ee16f60fafd3be7ea6f605d82d3f27c39704a3f875cbed5bd050dc70")
