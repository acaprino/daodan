const controller = {
  async webhook(req, res) {
    res.end();
  },
  list: (req, res) => res.json([]),
};
module.exports = controller;
