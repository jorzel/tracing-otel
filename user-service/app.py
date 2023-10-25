import time
from random import randint

from flask import Flask, jsonify
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

resource = Resource(
    attributes={
        "service.name": "user-service",
    }
)

provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="otel-collector:4317", insecure=True)
processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer("user-service")

app = Flask(__name__)


@app.route("/users/<string:username>/limits")
def reservation_limits(username):
    with tracer.start_as_current_span("reservation_limits"):
        _validate_username(username)
        record = _fetch_record(username)
        return jsonify(record)


@tracer.start_as_current_span("validate_username")
def _validate_username(username):
    time.sleep(0.1 * randint(0, 10))


@tracer.start_as_current_span("fetch_record")
def _fetch_record(username):
    time.sleep(0.1 * randint(0, 30))
    return {
        "username": username,
        "limits": {
            "reservations": len(username),
        },
    }
