from flask import Blueprint

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/users/<int:user_id>", methods=["GET", "POST"])
def user(user_id):
    return {"user": user_id}


@bp.get("/stats")
def stats():
    return {}
