// Every route an Express 4 app registers, read from the running app: the full path through every mount, the
// line that registers it and where its handler is defined. Runs only in the container, on the project's own
// express: node express_routes.js CHECKOUT APP_FILE OUT_JSON [EXPRESS_LIST_ENDPOINTS_DIR]
'use strict';
const path = require('path');
const fs = require('fs');
const inspector = require('inspector');
const { fileURLToPath } = require('url');

const [root, appFile, out, listDir] = process.argv.slice(2);
const load = require('module').createRequire(path.resolve(root, appFile));
const Router = load('express/lib/router');
const Route = load('express/lib/router/route');
const verbs = load('methods').concat('all');
const mounts = []; // [parent router, path, child router]
const routes = []; // {owner, path, method, handlers, site}

const rel = (file) => path.relative(root, file).split(path.sep).join('/');
function site() {
    for (const frame of new Error().stack.split('\n').slice(2)) {
        const m = frame.match(/\(?([^()\s]+):(\d+):\d+\)?$/);
        if (m && m[1] !== __filename && !m[1].includes('node_modules') && m[1].startsWith(root)) {
            return `${rel(m[1])}:${m[2]}`;
        }
    }
    return null;
}

const use = Router.use;
Router.use = function (first, ...rest) {
    const bare = typeof first === 'function';
    const paths = bare ? ['/'] : [].concat(first);
    for (const fn of (bare ? [first, ...rest] : rest).flat(Infinity)) {
        if (fn && Array.isArray(fn.stack)) paths.forEach((p) => mounts.push([this, String(p), fn]));
    }
    return use.apply(this, arguments);
};
const route = Router.route;
Router.route = function (p) {
    const made = route.call(this, p);
    made.__owner = this;
    made.__site = site();
    return made;
};
for (const verb of verbs) {
    const original = Route.prototype[verb];
    Route.prototype[verb] = function (...handlers) {
        routes.push({ owner: this.__owner, path: this.path, method: verb.toUpperCase(),
            handlers: handlers.flat(Infinity), site: this.__site });
        return original.apply(this, handlers);
    };
}

const join = (a, b) => (`${a.replace(/\/+$/, '')}/${b.replace(/^\/+/, '')}`).replace(/\/+$/, '') || '/';
function prefixes(router, top, seen) {
    if (router === top) return [''];
    if (seen.has(router)) return [];
    const out = [];
    for (const [parent, p, child] of mounts) {
        if (child === router) prefixes(parent, top, new Set([...seen, router])).forEach((pre) => out.push(join(pre, p)));
    }
    return out;
}

async function main() {
    const app = load(path.resolve(root, appFile));
    const session = new inspector.Session();
    session.connect();
    const scripts = {};
    session.on('Debugger.scriptParsed', ({ params }) => { scripts[params.scriptId] = params.url; });
    const post = (method, params) => new Promise((ok, ko) => session.post(method, params, (e, r) => (e ? ko(e) : ok(r))));
    await post('Debugger.enable');
    async function locate(fn) {
        globalThis.__connectionPoint = fn;
        const { result } = await post('Runtime.evaluate', { expression: 'globalThis.__connectionPoint' });
        const { internalProperties } = await post('Runtime.getProperties', { objectId: result.objectId });
        const where = (internalProperties || []).find((p) => p.name === '[[FunctionLocation]]');
        if (!where) return null;
        const url = scripts[where.value.value.scriptId] || '';
        const file = url.startsWith('file:') ? fileURLToPath(url) : url;
        const lines = Function.prototype.toString.call(fn).split('\n').length;
        const line = where.value.value.lineNumber + 1;
        return { file: file.startsWith(root) ? rel(file) : file, line, end: line + lines - 1 };
    }
    const top = app._router;
    const listed = [];
    for (const r of routes) {
        const handler = r.handlers[r.handlers.length - 1];
        const at = typeof handler === 'function' ? await locate(handler) : null;
        const bases = prefixes(r.owner, top, new Set());
        for (const local of [].concat(r.path)) {
            for (const base of bases.length ? bases : [null]) {
                listed.push({ method: r.method, path: base === null ? null : join(base, String(local)),
                    local: String(local), site: r.site, handler: { name: handler && handler.name, ...at },
                    mounted: base !== null });
            }
        }
    }
    const report = { routes: listed, mounts: mounts.length };
    if (listDir) {
        const list = require(path.join(listDir, 'node_modules', 'express-list-endpoints'));
        report.express_list_endpoints = list(app).map((e) => ({ path: e.path, methods: e.methods }));
    }
    fs.writeFileSync(out, JSON.stringify(report, null, 1));
    process.exit(0);
}
main().catch((error) => { fs.writeFileSync(out, JSON.stringify({ error: String(error.stack || error) })); process.exit(1); });
