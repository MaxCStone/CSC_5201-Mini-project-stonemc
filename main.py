import os
import json
import redis
from flask import Flask, jsonify, request

app = Flask(__name__)

redis_db = redis.Redis(
    host=os.environ.get("REDIS_HOST", "127.0.0.1"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    decode_responses=True,
)


@app.route("/cart/<user_id>", methods=["GET"])
def get_cart(user_id):
    cart = redis_db.get(f"cart:{user_id}")
    return jsonify({
        "user_id": user_id,
        "cart": json.loads(cart) if cart else None,
    })
    

@app.route("/cart/<user_id>", methods=["POST"])
def add_to_cart(user_id):
    item = request.get_json(silent=True)

    required_fields = {"product_id", "name", "description", "price_usd", "categories"}

    if not isinstance(item, dict) or set(item.keys()) != required_fields:
        return jsonify({
            "error": "JSON must contain only product_id, name, description, price_usd, and categories fields"
        }), 400

    if not isinstance(item["product_id"], str) or not item["product_id"]:
        return jsonify({"error": "product_id must be a non-empty string"}), 400

    if not isinstance(item["name"], str) or not item["name"]:
        return jsonify({"error": "name must be a non-empty string"}), 400

    if not isinstance(item["description"], str) or not item["description"]:
        return jsonify({"error": "description must be a non-empty string"}), 400
    
    if not isinstance(item["price_usd"], (int, float)) or isinstance(item["price_usd"], bool):
        return jsonify({"error": "price_usd must be a number"}), 400

    if item["price_usd"] < 0:
        return jsonify({"error": "price_usd cannot be negative"}), 400

    if (
        not isinstance(item["categories"], list)
        or not item["categories"]
        or not all(
            isinstance(category, str) and category.strip()
            for category in item["categories"]
        )
    ):
        return jsonify({
            "error": "categories must be a non-empty list of strings"
        }), 400

    cart_key = f"cart:{user_id}"
    stored_cart = redis_db.get(cart_key)
    cart = json.loads(stored_cart) if stored_cart else []

    cart.append(item)
    redis_db.set(cart_key, json.dumps(cart))

    return jsonify({
        "message": f"Item added to cart for user {user_id}",
        "item": item,
        "cart": cart,
    }), 201
    
@app.route("/cart/<user_id>", methods=["DELETE"])
def delete_cart(user_id):
    redis_db.delete(f"cart:{user_id}")
    return jsonify({
        "message": f"Cart deleted for user {user_id}"
    }), 200


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
    )