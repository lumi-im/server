from flask import Flask, abort, render_template, request, jsonify
from redis import Redis
import json
import random


app = Flask(__name__)
redis = Redis()


def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


def init_axolotl_database():
    redis.delete('lumi-identities')


@app.route("/")
def home():
    return render_template('home.html')


@app.route('/<identity>/')
def profile(identity):
    if not redis.sismember('lumi-identities', identity):
        abort(404)
    p = redis.hgetall(identity)
    prekeys = {int(k.decode('utf-8')): v.decode('utf-8') for k, v in p.items()}
    m = redis.lrange(identity + "-messages", 0, -1)
    messages = [json.loads(message.decode('utf-8')) for message in m]
    return render_template('identity.html',
            identity=identity, prekeys=prekeys, messages=messages)


@app.route('/<identity>/messages/', methods=['POST'])
def add_message(identity):
    if not redis.sismember('lumi-identities', identity):
        abort(404)
    redis.lpush(identity + "-messages", json.dumps(request.json))
    return 'hi'

@app.route('/<identity>/messages/oldest/')
def get_oldest_message(identity):
    if not redis.sismember('lumi-identities', identity):
        abort(404)
    test = redis.rpop(identity + "-messages")
    if test:
        return test
    else:
        abort(404)

@app.route('/<identity>/prekeys/', methods=['POST'])
def add_prekeys(identity):
    if not redis.sismember('lumi-identities', identity):
        abort(404)
    redis.hmset(identity, request.json)
    return ''


@app.route('/<identity>/prekeys/<id>/')
def get_prekey(identity, id):
    if not redis.sismember('lumi-identities', identity):
        abort(404)
    prekey = redis.hget(identity, id)
    redis.hdel(identity, id)
    return prekey


@app.route('/<identity>/prekeys/random/')
def get_random_prekey(identity):
    if not redis.sismember('lumi-identities', identity):
        abort(404)
    prekey_ids = redis.hkeys(identity)
    prekey_id = random.choice(prekey_ids)
    prekey = redis.hget(identity, prekey_id)
    redis.hdel(identity, prekey_id)
    return jsonify({'id': prekey_id, 'key': prekey})


@app.route('/identities/')
def identities():
    r = redis.smembers('lumi-identities')
    identities = []
    for identity in r:
        identities.append(identity.decode('utf-8'))
    if request_wants_json():
        return jsonify(identities=list(identities))
    else:
        return render_template('identities.html', identities=identities)


@app.route('/identities/', methods=['POST'])
def add_identity():
    if request.data:
        redis.sadd('lumi-identities', request.data)
    else:
        abort(400)
    return 'hi'


if __name__ == "__main__":
    init_axolotl_database()
    app.run(debug=True)
