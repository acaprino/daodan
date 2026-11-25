from flask import Flask

from sharedlib.views import shared_view

app = Flask(__name__)
app.add_url_rule("/shared", endpoint="shared", view_func=shared_view)


@app.get("/own")
def own():
    return "own"
