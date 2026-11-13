const logError = async (message) => {
  console.error(message);
};
const logInfo = function (message) {
  console.log(message);
};
module.exports = { logError, logInfo: logInfo, log: logError };
