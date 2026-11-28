const express = require('express');

const router = express.Router();

function list(req, res) {
  res.json([]);
}

function show(req, res) {
  res.json({});
}

function update(req, res) {
  res.json({});
}

router.get('/', list);
router.route('/:id').get(show).post(update);

module.exports = router;
