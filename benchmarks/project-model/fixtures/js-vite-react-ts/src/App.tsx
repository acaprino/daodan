import { Button } from "@/components/Button";
import { money } from "@/lib/format";

export default function App() {
  return <Button label={money(5)} />;
}
