function adminPage(req, res) {
  res.end();
}

function admin(router) {
  router.get('/admin', adminPage);
}

function mountAll(app, router) {
  admin(router);
  app.use('/api', router);
}

module.exports = { mountAll };
