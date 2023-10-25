import logging
import os
import time
from dataclasses import dataclass
from random import randint

import requests
from flask import Flask, jsonify, request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import \
    TraceContextTextMapPropagator

SERVICE_NAME = "reservations-service"
OTEL_COLLECTOR_ENDPOINT = os.environ.get("OTEL_COLLECTOR_ENDPOINT", "localhost:4317")
USER_SERVICE_URL = os.environ["USER_SERVICE_URL"]

resource = Resource(
    attributes={
        "service.name": SERVICE_NAME,
    }
)

provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint=OTEL_COLLECTOR_ENDPOINT, insecure=True)
processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(SERVICE_NAME)

app = Flask(__name__)


@dataclass(frozen=True)
class ReservationCommand:
    username: str
    item_id: str


@app.route("/reservations", methods=["POST"])
def reservations():
    with tracer.start_as_current_span("reservations_handler"):
        command = _parse_request(request)
        carrier = {}
        TraceContextTextMapPropagator().inject(carrier=carrier)
        limit = _fetch_limit(command.username, carrier)
        if limit <= 0:
            return jsonify("failure, limit not found")
        reservations_count = _fetch_reservations_count(command.username)
        if reservations_count > limit:
            return jsonify("failure, limit exceeded")
        _make_reservation(command.username, command.item_id)
    return jsonify("success")


@tracer.start_as_current_span("parse_request")
def _parse_request(request):
    time.sleep(0.01 * randint(0, 4))
    return ReservationCommand(
        username=request.json["username"],
        item_id=request.json["item_id"],
    )


@tracer.start_as_current_span("fetch_limit")
def _fetch_limit(username, carrier):
    url = f"{USER_SERVICE_URL}/users/{username}/limits"
    try:
        response = requests.get(url, timeout=10, headers=carrier)
        logging.info("Send request with headers: {}".format(carrier))
        return response.json()["limits"]["reservations"]
    except Exception:
        logging.exception("Error fetching limit for user {}".format(username))
        return -1


@tracer.start_as_current_span("fetch_reservations_count")
def _fetch_reservations_count(username):
    time.sleep(0.07 * randint(0, 8))
    return randint(0, 7)


@tracer.start_as_current_span("make_reservation")
def _make_reservation(username, item_id):
    time.sleep(0.03 * randint(0, len(item_id) + 2))
