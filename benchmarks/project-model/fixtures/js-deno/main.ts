import chalk from "chalk";
import ms from "ms";
import { greet } from "@/util.ts";

console.log(chalk.green(greet("deno")), ms("2s"));
