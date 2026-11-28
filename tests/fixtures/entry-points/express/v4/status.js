function mountStatus(router) {
  router.get('/status', (req, res) => res.json({ ok: true }));
}

module.exports.mountStatus = mountStatus;
