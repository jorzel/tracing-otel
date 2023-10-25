import os
import time
from random import randint

from flask import Flask, jsonify, request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import \
    TraceContextTextMapPropagator

SERVICE_NAME = "user-service"
OTEL_COLLECTOR_ENDPOINT = os.environ.get("OTEL_COLLECTOR_ENDPOINT", "localhost:4317")

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


@app.route("/users/<string:username>/limits")
def reservation_limits(username):
    ctx = TraceContextTextMapPropagator().extract(carrier=request.headers)
    with tracer.start_as_current_span("reservation_limits_handler", context=ctx):
        _validate_username(username)
        record = _fetch_record(username)
    return jsonify(record)


@tracer.start_as_current_span("validate_username")
def _validate_username(username):
    time.sleep(0.04 * randint(0, 10))


@tracer.start_as_current_span("fetch_record")
def _fetch_record(username):
    time.sleep(0.1 * randint(0, 6))
    return {
        "username": username,
        "limits": {
            "reservations": len(username),
        },
    }
