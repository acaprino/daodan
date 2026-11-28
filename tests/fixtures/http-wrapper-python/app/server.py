# The routes the project offers, through a router of its own.


class Router:
    def get(self, path, handler):
        return handler

    def post(self, path, handler):
        return handler

    def put(self, path, handler):
        return handler


router = Router()


def list_users():
    return []


def create_order():
    return {}


def replace_order():
    return {}


router.get("/api/users", list_users)
router.post("/api/orders", create_order)
router.put("/api/orders", replace_order)
