import json
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

        data = recvlines(s, 1)
        response:dict = eval(data[0].decode())
        if error:=response.get("error"):
            raise Exception(error)
        print(data)
        print(response)
    return response

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
    session["data"] = creds
    return creds

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
    app.run("0.0.0.0", PROXY_PORT, debug=True)
