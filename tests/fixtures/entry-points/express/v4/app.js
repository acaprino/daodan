const express = require('express');
const users = require('./routes/users');
const { health } = require('./handlers');
const { mountStatus } = require('./status');

const app = express();
const api = express.Router();

function check(req, res, next) {
  next();
}

api.use('/users', users);
app.use('/api/v1', api);
mountStatus(api);
app.get('/health', health);
app.post('/login', (req, res) => {
  res.send('ok');
});
app.get('/multi', [check, function multi(req, res) {
  res.end();
}]);
app.put('/checked', check, (req, res) => res.end());
const base = '/x' + process.env.PREFIX;
app.get(base, (req, res) => res.end());
app.use(process.env.MOUNT, users);
app.get('env');

module.exports = app;
require('fs').writeFileSync(require('path').join(__dirname, 'ran.txt'), 'the app ran');
