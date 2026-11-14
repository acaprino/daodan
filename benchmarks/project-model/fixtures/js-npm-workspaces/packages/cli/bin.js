#!/usr/bin/env node
const core = require("@acme/core");
const kleur = require("kleur");

console.log(kleur.green(String(core.last([1, 2, 3]))));
