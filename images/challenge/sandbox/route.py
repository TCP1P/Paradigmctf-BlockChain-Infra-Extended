import os
import re
from flask import Flask, Response, request, session, send_file
from flask_limiter import Limiter
from random import randbytes
from flask_limiter.util import get_remote_address
import requests
import re
import os
from .env import SESSION_COOKIE_NAME, SECRET_KEY
from .ppow import Challenge, check
from .blockchain_manager import *

UUID_PATTERN = re.compile(r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$')
ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9]{1,}$')
DISABLE_TICKET = os.getenv("DISABLE_TICKET", "false").lower() == "true"
ETH_ALLOWED_NAMESPACES = ["web3", "eth", "net"]
CAIRO_ALLOWED_NAMESPACES = ["starknet"]

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_NAME'] = SESSION_COOKIE_NAME

CHALLENGE_LEVEL = 10000

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

@app.before_request
def before_request():
    challenge = session.get("challenge")
    if DISABLE_TICKET:
        if not session.get("ticket"): 
            session["ticket"] = randbytes(16).hex()
    if challenge == None:
        challenge = Challenge.generate(CHALLENGE_LEVEL)
        session["challenge"] = str(challenge)

@app.post("/solution")
def send_solution():
    challenge = session.get("challenge")
    solution = request.json.get("solution")
    try:
        if not check(Challenge.from_string(challenge) , solution):
            session['challenge'] = str(Challenge.generate(CHALLENGE_LEVEL))
            raise Exception("challenge failed")
    except:
        session['challenge'] = str(Challenge.generate(CHALLENGE_LEVEL))
        raise Exception("challenge failed")
    session["ticket"] = randbytes(16).hex()
    session.pop("challenge")
    return message("challenge solved")

@app.get("/data")
def get_instance_data():
    return session.get("data", {})

@app.get("/challenge")
def get_challenge():
    return {"challenge": session.get("challenge")}

@app.get("/")
def home():
    return send_file("index.html")

@app.route("/<string:uuid>", methods=["POST"])
def proxy(uuid):
    if not is_uuid(uuid):
        raise Exception("uuid is not a valid uuid")
    body = request.get_json()
    if not body:
        return "invalid content type, only application/json is supported"
    if not has_instance_by_uuid(uuid):
        return {
            "jsonrpc": "2.0",
            "id": body["id"],
            "error": {
                "code": -32602,
                "message": "invalid uuid specified",
            },
        }
    if BM.blockchain_type == "eth":
        if "method" not in body or not isinstance(body["method"], str):
            return {
                "jsonrpc": "2.0",
                "id": body["id"],
                "error": {
                    "code": -32600,
                    "message": "invalid request",
                },
            }
        ok = (
            any(body["method"].startswith(namespace) for namespace in ETH_ALLOWED_NAMESPACES)
            and body["method"] != "eth_sendUnsignedTransaction"
        )
        if not ok:
            return {
                "jsonrpc": "2.0",
                "id": body["id"],
                "error": {
                    "code": -32600,
                    "message": "invalid request",
                },
            }

    node_info = get_instance_by_uuid(uuid)
    resp = requests.post(f"http://127.0.0.1:{node_info.port}/", json=body)
    response = Response(resp.content, resp.status_code, resp.raw.headers.items())
    return response
