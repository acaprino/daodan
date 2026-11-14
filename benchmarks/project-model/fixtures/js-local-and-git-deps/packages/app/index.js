const { id } = require("@acme/lib");
const isNumber = require("is-number");

module.exports = (x) => isNumber(id(x));
