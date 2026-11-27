const { logError: report, logInfo } = require('./logService');
class AppError extends Error {}
function fail() {
  report('x');
  logInfo('y');
  throw new Error('z');
}
module.exports = { fail, AppError };
