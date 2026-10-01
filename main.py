import os
from flask import Flask, jsonify
import redis

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
        "cart": cart
    })
    
@app.route("/cart/<user_id>", methods=["POST"])
def add_to_cart(user_id):
    redis_db.set(f"cart:{user_id}", "item1, item2, item3")
    return jsonify({
        "message": f"Items added to cart for user {user_id}"
    }), 201


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
    )