import os

import requests
from flask import Flask, jsonify
from opentelemetry import trace
from opentelemetry.propagate import inject

from tracing import setup_tracing

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "order-service")
SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://service-b:8080")

setup_tracing(SERVICE_NAME)

app = Flask(__name__)
tracer = trace.get_tracer(SERVICE_NAME)


def build_order_response() -> dict:
    order = {
        "id": 42,
        "product": "Кольцо с александритом",
        "price": 150_000,
        "quantity": 2,
    }

    with tracer.start_as_current_span("fetch_order_total") as span:
        span.set_attribute("order.id", order["id"])
        headers = {}
        inject(headers)
        with tracer.start_as_current_span("call_calculation_service") as client_span:
            client_span.set_attribute("http.url", f"{SERVICE_B_URL}/calculate")
            response = requests.get(
                f"{SERVICE_B_URL}/calculate",
                params={"price": order["price"], "quantity": order["quantity"]},
                headers=headers,
                timeout=5,
            )
            client_span.set_attribute("http.status_code", response.status_code)
        response.raise_for_status()
        calculation = response.json()

    return {
        "order": order,
        "calculation": calculation,
    }


@app.get("/")
def root():
    with tracer.start_as_current_span("get_order"):
        return jsonify(build_order_response())


@app.get("/order")
def get_order():
    with tracer.start_as_current_span("get_order"):
        return jsonify(build_order_response())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
