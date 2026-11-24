from flask import Blueprint

bp = Blueprint("admin", __name__, url_prefix="/admin")
assets = Blueprint("assets", __name__, url_prefix="/assets", static_folder="files")


@bp.route("/users/<int:user_id>", methods=["GET", "POST"])
def user(user_id):
    return {"user": user_id}


@bp.get("/stats")
def stats():
    return {}


def make_blueprint():
    nested = Blueprint("nested", __name__, url_prefix="/nested")

    @nested.get("/inner")
    def inner():
        return "inner"

    return nested
