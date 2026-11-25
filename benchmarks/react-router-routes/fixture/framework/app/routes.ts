import { type RouteConfig, index, layout, prefix, route } from "@react-router/dev/routes";

// routes.ts is code: a loop writes two routes of one module, with an id each
const LOCALES = ["en", "it"];

export default [
  index("routes/home.tsx"),
  route("about", "routes/about.tsx"),
  layout("routes/shop/layout.tsx", [
    route("checkout", "routes/shop/checkout.tsx"),
    route("orders/:id", "routes/shop/order.tsx"),
  ]),
  ...prefix("api", [
    route("pay", "routes/api/pay.ts"),
    route("health", "routes/api/health.ts"),
  ]),
  route("docs/*", "routes/docs.tsx"),
  route(":lang?/blog", "routes/blog.tsx"),
  route("users/:id", "routes/users/user.tsx", { id: "user-detail" }),
  route("users/:id/edit", "routes/users/edit.tsx", { id: "user-edit", caseSensitive: true }),
  route("nested", "routes/nested/layout.tsx", [
    index("routes/nested/index.tsx"),
    route("child", "routes/nested/child.tsx"),
  ]),
  route("legacy", "routes/legacy.jsx"),
  ...LOCALES.map((locale) => route(`${locale}/hello`, "routes/hello.tsx", { id: `hello-${locale}` })),
] satisfies RouteConfig;
