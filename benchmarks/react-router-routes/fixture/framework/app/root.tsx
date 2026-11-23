import { Outlet } from "react-router";

export default function App() {
  return <Outlet />;
}

export function ErrorBoundary() {
  return <p>Something went wrong</p>;
}
