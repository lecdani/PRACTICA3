import time
import redis
from flask import Flask, jsonify, request

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

def decode_dict(dictionary):
    return {key.decode('utf-8'): value.decode('utf-8') for key, value in dictionary.items()}

def get_directories():
    directory_ids = cache.smembers('directories')
    directories = []
    for directory_id in directory_ids:
        directory = cache.hgetall(directory_id)
        directory = decode_dict(directory)
        directories.append(directory)
    return directories

@app.route('/')
def hello():
    count = get_hit_count()
    return 'Hello World! I have been seen {} times.\n'.format(count)

@app.route('/status/', methods=['GET'])
def get_status():
    return 'pong'

@app.route('/directories/', methods=['GET'])
def get_directories_route():
    directories = get_directories()
    return jsonify({"count": len(directories), "results": directories})

@app.route('/directories/', methods=['POST'])
def create_directory():
    directory_data = request.json
    directory_id = cache.incr('directory_id')
    directory_key = f'directory:{directory_id}'
    cache.hset(directory_key, "id", directory_id)
    cache.hset(directory_key, "name", directory_data["name"])
    cache.hset(directory_key, "emails", directory_data["emails"])
    cache.sadd('directories', directory_key)
    new_directory = cache.hgetall(directory_key)
    new_directory = decode_dict(new_directory)
    return jsonify(new_directory), 201

@app.route('/directories/<int:id>', methods=['GET'])
def get_directory(id):
    directory_key = f'directory:{id}'
    directory = cache.hgetall(directory_key)
    if directory:
        directory = decode_dict(directory)
        return jsonify(directory)
    else:
        return jsonify({"error": "Directory not found"}), 404

@app.route('/directories/<int:id>', methods=['PUT'])
def update_directory(id):
    directory_data = request.json
    directory_key = f'directory:{id}'
    if cache.exists(directory_key):
        cache.hset(directory_key, "name", directory_data["name"])
        cache.hset(directory_key, "emails", directory_data["emails"])
        updated_directory = cache.hgetall(directory_key)
        updated_directory = decode_dict(updated_directory)
        return jsonify(updated_directory)
    else:
        return jsonify({"error": "Directory not found"}), 404

@app.route('/directories/<int:id>', methods=['PATCH'])
def partially_update_directory(id):
    directory_data = request.json
    directory_key = f'directory:{id}'
    if cache.exists(directory_key):
        if "name" in directory_data:
            cache.hset(directory_key, "name", directory_data["name"])
        if "emails" in directory_data:
            cache.hset(directory_key, "emails", directory_data["emails"])
        updated_directory = cache.hgetall(directory_key)
        updated_directory = decode_dict(updated_directory)
        return jsonify(updated_directory)
    else:
        return jsonify({"error": "Directory not found"}), 404

@app.route('/directories/<int:id>', methods=['DELETE'])
def delete_directory(id):
    directory_key = f'directory:{id}'
    if cache.exists(directory_key):
        cache.srem('directories', directory_key)
        cache.delete(directory_key)
        return jsonify({"message": "Directory deleted"})
    else:
        return jsonify({"error": "Directory not found"}), 404