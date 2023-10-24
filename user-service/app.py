import time
from random import randint

from flask import Flask, jsonify
from opentelemetry import trace

app = Flask(__name__)

tracer = trace.get_tracer("my.tracer.name")


@app.route("/users/<string:username>/limits")
def reservation_limits(username):
    record = _fetch_record(username)
    return jsonify(record)


def _fetch_record(username):
    time.sleep(randint(0, 3))
    return {
        "username": username,
        "limits": {
            "reservations": len(username),
        },
    }
