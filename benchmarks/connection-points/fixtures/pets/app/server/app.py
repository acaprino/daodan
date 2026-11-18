from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/api/dogs', methods=['GET'])
def get_dogs():
    return jsonify([])


@app.route('/api/dogs/<int:id>', methods=['GET'])
def get_dog(id):
    return jsonify({"id": id})


@app.route('/api/breeds/<int:id>', methods=['GET'])
def get_breed(id):
    return jsonify({"id": id})


@app.route('/api/breeds/<name>', methods=['GET'])
def get_breed_by_name(name):
    return jsonify({"name": name})


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"ok": True})
