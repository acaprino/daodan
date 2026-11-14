const express = require('express');
const logger = require('./logService');
const billingModule = require('./billing');
const controller = require('./controller');
const { json } = express;
function run(flag, callback, req, res) {
  billingModule.webhookHandler(req, res);
  logger.logError('a');
  logger.logInfo('b');
  logger.log('c');
  controller.webhook(req, res);
  controller.list(req, res);
  const pick = flag ? logger.logError : logger.logInfo;
  pick('d');
  const same = logger.logError;
  same('e');
  callback('f');
  const made = makeHandler();
  made('g');
  json();
}
function makeHandler() {
  return () => 1;
}
module.exports = { run };
