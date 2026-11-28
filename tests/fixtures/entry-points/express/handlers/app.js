const express = require('express');
const limit = require('express-rate-limit');
const controller = require('./controller');
const Tasks = require('./tasks');
const catchAsync = require('./catch');
const { basket } = require('./factory');
const { mountAll } = require('./mount');

const app = express();
const tasks = new Tasks();
const api = express.Router();

app.get('/items', controller.list);
app.get('/tasks', tasks.all);
app.get('/tasks/done', tasks.done);
app.post('/wrapped', catchAsync(async (req, res) => {
  res.end();
}));
app.get('/wrapped/items', catchAsync(controller.list));
app.get('/basket', basket());
app.get('/limited', limit());
mountAll(app, api);
const users = require('./users');
app.post('/users', users.create);
app.get('/wrapped/basket', catchAsync(basket()));
app.get('/wrapped/limited', catchAsync(limit()));

module.exports = app;
require('fs').writeFileSync(require('path').join(__dirname, 'ran.txt'), 'the app ran');
