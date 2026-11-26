/** @type {import('@remix-run/dev').AppConfig} */
module.exports = {
  ignoredRouteFiles: ["**/.*"],
  // remix.config.js is code: it adds a route the file convention does not name
  routes(defineRoutes) {
    return defineRoutes((route) => {
      route("custom/:id", "custom.tsx", { id: "custom-route" });
    });
  },
};
