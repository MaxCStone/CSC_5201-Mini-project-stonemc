# Copyright 2020 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
import os
from flask import Flask
import redis

app = Flask(__name__)
redis_dbr = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "Worlda")
    return f"Hello {name}!"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


