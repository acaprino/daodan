from flask import Flask

from app.blueprint import bp

app = Flask(__name__)
app.register_blueprint(bp)


@app.route("/")
def index():
    return "index"


@app.post("/items")
def create_item():
    return "created"


class Pages:
    def show(self):
        return "page"


app.add_url_rule("/page", view_func=Pages().show)
app.add_url_rule("/lambda", endpoint="lam", view_func=lambda: "lam")
