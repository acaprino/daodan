const catchAsync = require('./catch');

const create = catchAsync(async (req, res) => {
  res.end();
});

module.exports = { create };
