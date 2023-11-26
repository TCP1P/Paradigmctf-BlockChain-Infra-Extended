import os
import socket
from flask import Flask, Response, request, session, send_file
from flask_limiter import Limiter
from flask_cors import cross_origin
from random import randbytes
from flask_limiter.util import get_remote_address
import requests

HTTP_PORT = os.getenv("HTTP_PORT", "8545")
PROXY_PORT = os.getenv("PROXY_PORT", "8545")

app = Flask(__name__)
app.secret_key = randbytes(32)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["60 per minute"],
    storage_uri="memory://",
)

def message(msg):
    return {"message": msg}

def recvline(s: socket.socket):
    data = b""
    while (needle := s.recv(1)) != b"\n":
        data += needle
    return data

def recvlines(s: socket.socket, num):
    result: list[bytes] = []
    for _ in range(num):
        result.append(recvline(s))
    return result

def send_action_and_ticket(action, ticket):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', 31337))
        s.sendall(f"{action}\n".encode())
        s.sendall(f"{ticket}\n".encode())

        data = recvlines(s, 5)
        response = data[4].decode()
        if response != "":
            raise Exception(response)
        data = recvlines(s, 7)
        msg = (data[1] + b" " + data[2]).decode()
        uuid = data[3].split()[-1].decode()
        rpc_endpoint = data[4].split()[-1].decode()
        private_key = data[5].split()[-1].decode()
        setup_contract = data[6].split()[-1].decode()
    return uuid, rpc_endpoint, private_key, setup_contract, msg

@app.get("/ticket/<string:ticket>")
def save_ticket(ticket):
    session["ticket"] = ticket
    return message("ticket saved")

def default_action(action):
    ticket = session.get("ticket")
    if not ticket:
        return message("Please add a ticket"), 400
    try:
        creds = send_action_and_ticket(action, ticket)
    except Exception as e:
        return message(str(e)), 500
    uuid, rpc_endpoint, private_key, setup_contract, msg = creds
    data = {
        "uuid": uuid,
        "rpc_endpoint": rpc_endpoint,
        "private_key": private_key,
        "setup_contract": setup_contract,
        "message": msg
    }
    session["data"] = data
    return data

@app.get("/instance/data")
def get_instance_data():
    return session.get("data", {})

@app.get("/instance/launch")
@limiter.limit("10 per minute")
def launch():
    return default_action(1)

@app.get("/instance/kill")
@limiter.limit("10 per minute")
def kill():
    session["data"] = {}
    return default_action(2)

@app.get("/instance/flag")
@limiter.limit("10 per minute")
def flag():
    return default_action(3)

@app.get("/")
def home():
    return send_file("index.html")

@app.route("/<string:uuid>", methods=["POST"])
@cross_origin()
def proxy(uuid):
    body = request.get_json()
    resp = requests.post(f"http://127.0.0.1:{HTTP_PORT}/{uuid}", json=body)
    response = Response(resp.content, resp.status_code, resp.raw.headers.items())
    return response

@app.route("/download/solver-pow.py")
def download_solver_pow():
    file_path = "solver-pow.py"
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run("0.0.0.0", PROXY_PORT)
