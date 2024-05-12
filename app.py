import time

import redis
from flask import Flask,  jsonify, request

app = Flask(__name__)
cache = redis.Redis(host='redis', port=6379, db=0)

def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)

@app.route('/')
def hello():
    count = get_hit_count()
    return 'Hello World! I have been seen {} times.\n'.format(count)

@app.route('/status/', methods=['GET'])
def get_status():
    return 'pong'

directories = []

@app.route('/directories/', methods=['GET'])
def get_directories():
    return jsonify({"count": len(directories), "results": directories})


@app.route('/directories/', methods=['POST'])
def create_directory():
    directory_data = request.json
    new_directory = {
        "id": len(directories) + 1,
        "name": directory_data["name"],
        "emails": directory_data["emails"]
    }
    directories.append(new_directory)
    return jsonify(new_directory), 201


@app.route('/directories/<int:id>', methods=['GET'])
def get_directory(id):
    directory = next((directory for directory in directories if directory["id"] == id), None)
    if directory:
        return jsonify(directory)
    else:
        return jsonify({"error": "Directory not found"}), 404


@app.route('/directories/<int:id>', methods=['PUT'])
def update_directory(id):
    directory_data = request.json
    directory = next((directory for directory in directories if directory["id"] == id), None)
    if directory:
        directory["name"] = directory_data["name"]
        directory["emails"] = directory_data["emails"]
        return jsonify(directory)
    else:
        return jsonify({"error": "Directory not found"}), 404


@app.route('/directories/<int:id>', methods=['PATCH'])
def partially_update_directory(id):
    directory_data = request.json
    directory = next((directory for directory in directories if directory["id"] == id), None)
    if directory:
        if "name" in directory_data:
            directory["name"] = directory_data["name"]
        if "emails" in directory_data:
            directory["emails"] = directory_data["emails"]
        return jsonify(directory)
    else:
        return jsonify({"error": "Directory not found"}), 404


@app.route('/directories/<int:id>', methods=['DELETE'])
def delete_directory(id):
    directory = next((directory for directory in directories if directory["id"] == id), None)
    if directory:
        directories.remove(directory)
        return jsonify({"message": "Directory deleted"})
    else:
        return jsonify({"error": "Directory not found"}), 404
