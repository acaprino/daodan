const express = require('express');
const controller = require('./controller');
const router = express.Router();
router.get('/tasks', async (req, res) => {
    res.end();
});
router.patch('/task/:uid', controller.update);
['/a', '/b'].forEach((p) => router.all(p, (req, res) => res.end()));
module.exports = router;
