import clsx from "clsx";
import { toMs } from "@acme/shared";

export const cls = clsx("a", { b: toMs("1s") > 0 });
