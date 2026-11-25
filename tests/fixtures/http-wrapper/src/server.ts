// The routes the project offers, through a router of its own.

const router = {
  get(_path: string, _handler: () => void) {},
  post(_path: string, _handler: () => void) {},
  put(_path: string, _handler: () => void) {},
  patch(_path: string, _handler: () => void) {},
  delete(_path: string, _handler: () => void) {},
};

function listPing() {}
function createOrder() {}
function putUser() {}
function removeItem() {}
function patchSecond() {}
function showWindow() {}

router.get('/api/ping', listPing);
router.post('/api/orders', createOrder);
router.put('/api/users', putUser);
router.delete('/api/items/{id}', removeItem);
router.patch('/api/second', patchSecond);
router.get('/api/window', showWindow);
