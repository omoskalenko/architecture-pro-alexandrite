import os

from flask import Flask, jsonify, request
from opentelemetry import trace
from opentelemetry.propagate import extract

from tracing import setup_tracing

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "calculation-service")

setup_tracing(SERVICE_NAME)

app = Flask(__name__)
tracer = trace.get_tracer(SERVICE_NAME)


@app.get("/calculate")
def calculate():
    context = extract(request.headers)

    with tracer.start_as_current_span("calculate_total", context=context) as span:
        price = float(request.args.get("price", 100))
        quantity = int(request.args.get("quantity", 1))
        span.set_attribute("order.price", price)
        span.set_attribute("order.quantity", quantity)
        total = price * quantity
        span.set_attribute("order.total", total)

    return jsonify(
        {
            "price": price,
            "quantity": quantity,
            "total": total,
            "currency": "RUB",
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
