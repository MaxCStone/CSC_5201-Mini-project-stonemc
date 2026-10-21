import os
import json
import redis
from google.cloud import logging
from flask import Flask, jsonify, request
# trigger rebuilding with this comment
app = Flask(__name__)
client = logging.Client()
logger = client.logger("cart-service")
client.setup_logging()  

redis_db = redis.Redis(
    host=os.environ.get("REDIS_HOST", "127.0.0.1"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    decode_responses=True,
    socket_connect_timeout=float(
        os.environ.get("REDIS_SOCKET_CONNECT_TIMEOUT", "5")
    ),
    socket_timeout=float(os.environ.get("REDIS_SOCKET_TIMEOUT", "5")),
)


@app.errorhandler(redis.exceptions.RedisError)
def handle_redis_error(error):
    app.logger.exception("Redis operation failed", exc_info=error)
    return jsonify({
        "error": "Cart service is temporarily unavailable"
    }), 503


@app.route("/cart/<user_id>", methods=["GET"])
def get_cart(user_id):
    log_string = f"user_id: {user_id} | cart | {request.method} | Correlation ID: {request.headers.get('correlation_id', 'N/A')} | INFO: Retrieving cart"
    logger.log_text(log_string)
    cart = redis_db.get(f"cart:{user_id}")
    return jsonify({
        "user_id": user_id,
        "cart": json.loads(cart) if cart else None,
    })
    

@app.route("/cart/<user_id>", methods=["POST"])
def add_to_cart(user_id):
    log_string = f"user_id: {user_id} | cart | {request.method} | Correlation ID: {request.headers.get('correlation_id', 'N/A')} | "
    
    item = request.get_json(silent=True)

    required_fields = {"product_id", "name", "description", "categories"}

    if not isinstance(item, dict):
        log_string += "ERROR: Invalid JSON structure"
        logger.log_text(log_string)
        return jsonify({
            "error": "JSON must contain product_id, name, description, price or price_usd, and categories fields"
        }), 400

    price_fields = {"price", "price_usd"} & item.keys()
    if (
        not required_fields.issubset(item)
        or set(item) != required_fields | price_fields
        or len(price_fields) != 1
    ):
        log_string += "ERROR: Invalid JSON structure"
        logger.log_text(log_string)
        return jsonify({
            "error": "JSON must contain only product_id, name, description, categories, and exactly one of price or price_usd"
        }), 400

    if "price" in item:
        item["price_usd"] = item.pop("price")

    if not isinstance(item["product_id"], str) or not item["product_id"]:
        log_string += "ERROR: Invalid product_id"
        logger.log_text(log_string)
        return jsonify({"error": "product_id must be a non-empty string"}), 400

    if not isinstance(item["name"], str) or not item["name"]:
        log_string += "ERROR: Invalid name"
        logger.log_text(log_string)
        return jsonify({"error": "name must be a non-empty string"}), 400

    if not isinstance(item["description"], str) or not item["description"]:
        log_string += "ERROR: Invalid description"
        logger.log_text(log_string)
        return jsonify({"error": "description must be a non-empty string"}), 400
    
    if not isinstance(item["price_usd"], (int, float)) or isinstance(item["price_usd"], bool):
        log_string += "ERROR: Invalid price_usd"
        logger.log_text(log_string)
        return jsonify({"error": "price_usd must be a number"}), 400

    if item["price_usd"] < 0:
        log_string += "ERROR: Negative price_usd"
        logger.log_text(log_string)
        return jsonify({"error": "price_usd cannot be negative"}), 400

    if (
        not isinstance(item["categories"], list)
        or not item["categories"]
        or not all(
            isinstance(category, str) and category.strip()
            for category in item["categories"]
        )
    ):
        log_string += "ERROR: Invalid categories"
        logger.log_text(log_string)
        return jsonify({
            "error": "categories must be a non-empty list of strings"
        }), 400

    cart_key = f"cart:{user_id}"
    stored_cart = redis_db.get(cart_key)
    cart = json.loads(stored_cart) if stored_cart else []

    cart.append(item)
    redis_db.set(cart_key, json.dumps(cart))

    log_string += "INFO: Item added to cart"
    logger.log_text(log_string)

    return jsonify({
        "message": f"Item added to cart for user {user_id}",
        "item": item,
        "cart": cart,
    }), 201
    
@app.route("/cart/<user_id>", methods=["DELETE"])
def delete_cart(user_id):
    redis_db.delete(f"cart:{user_id}")
    log_string = f"user_id: {user_id} | cart | {request.method} | Correlation ID: {request.headers.get('correlation_id', 'N/A')} | INFO: Cart deleted"
    logger.log_text(log_string)
    return jsonify({
        "message": f"Cart deleted for user {user_id}"
    }), 200


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
    )