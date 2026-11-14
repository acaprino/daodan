const clsx = require("clsx");
const { seconds } = require("@acme/lib");

module.exports = clsx("x", { y: seconds("2s") === 2 });
