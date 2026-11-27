const logError = async (message) => {
  console.error(message);
};
const alias = require('./alias');
const logNotice = function (message) {
  console.log(message);
  alias.fail();
};
module.exports = { logError, logInfo: logNotice, log: logError };
