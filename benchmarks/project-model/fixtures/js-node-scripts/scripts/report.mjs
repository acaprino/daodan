import { readFileSync } from "node:fs";
import { stamp } from "./lib.js";

console.log(stamp(readFileSync(process.argv[2], "utf8").length));
