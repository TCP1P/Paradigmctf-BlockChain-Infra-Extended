import os
import re
from flask import Flask, Response, request, session, send_file
from flask_limiter import Limiter
from flask_cors import cross_origin
from random import randbytes
from flask_limiter.util import get_remote_address
import requests
import re

HTTP_PORT = os.getenv("HTTP_PORT", "8545")
LAUNCHER_PORT = os.getenv("LAUNCHER_PORT", "8546")
PROXY_PORT = os.getenv("PROXY_PORT", "8080")

UUID_PATTERN = re.compile(r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$')
ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9]{1,}$')

app = Flask(__name__)
app.secret_key = randbytes(32)
app.config['SESSION_COOKIE_NAME'] = "blockchain_"+randbytes(6).hex()

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["60 per minute"],
    storage_uri="memory://",
)

def is_uuid(text):
    return bool(UUID_PATTERN.match(text))

def is_alphanumeric(text):
    return bool(ALPHANUMERIC_PATTERN.match(text))

def message(msg):
    return {"message": msg}

@app.get("/ticket/<string:ticket>")
def save_ticket(ticket):
    if not is_alphanumeric(ticket):
        return message("ticket is not alphanumeric")
    session["ticket"] = ticket
    return message("ticket saved")

@app.get("/instance/data")
def get_instance_data():
    return session.get("data", {})

@app.get("/instance/<string:path>")
@limiter.limit("10 per minute")
def launch(path):
    if not is_alphanumeric(path):
        return message("path is not alphanumeric")
    resp = requests.get(f"http://127.0.0.1:{LAUNCHER_PORT}/{path}", params={"ticket":session.get("ticket")})
    response = Response(resp.content, resp.status_code, resp.raw.headers.items())
    return response

@app.get("/")
def home():
    return send_file("index.html")

@app.route("/<string:uuid>", methods=["POST"])
@cross_origin()
def proxy(uuid):
    if not is_uuid(uuid):
        return message("uuid is not a valid uuid")
    body = request.get_json()
    resp = requests.post(f"http://127.0.0.1:{HTTP_PORT}/{uuid}", json=body)
    response = Response(resp.content, resp.status_code, resp.raw.headers.items())
    return response

@app.route("/download/solver-pow.py")
def download_solver_pow():
    file_path = "solver-pow.py"
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run("0.0.0.0", PROXY_PORT, debug=True)
