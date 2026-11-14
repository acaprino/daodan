#!/usr/bin/env node
import { parse } from "../src/index.mjs";

console.log(parse(process.argv[2] ?? "1s"));
