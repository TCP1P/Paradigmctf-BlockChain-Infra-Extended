import os
import random
import subprocess
import signal
import json
import time
from threading import Thread
from typing import Dict
from uuid import uuid4
import re
import asyncio
import requests
from flask import Flask, Response, request
from flask_cors import CORS, cross_origin
from starknet_py.net.full_node_client import FullNodeClient

app = Flask(__name__)
CORS(app)

HTTP_PORT = os.getenv("HTTP_PORT", "8545")

try:
    os.mkdir("/tmp/instances-by-team")
    os.mkdir("/tmp/instances-by-uuid")
except:
    pass


def has_instance_by_uuid(uuid: str) -> bool:
    return os.path.exists(f"/tmp/instances-by-uuid/{uuid}")


def has_instance_by_team(team: str) -> bool:
    return os.path.exists(f"/tmp/instances-by-team/{team}")


def get_instance_by_uuid(uuid: str) -> Dict:
    with open(f"/tmp/instances-by-uuid/{uuid}", "r") as f:
        return json.loads(f.read())


def get_instance_by_team(team: str) -> Dict:
    with open(f"/tmp/instances-by-team/{team}", "r") as f:
        return json.loads(f.read())


def delete_instance_info(node_info: Dict):
    os.remove(f'/tmp/instances-by-uuid/{node_info["uuid"]}')
    os.remove(f'/tmp/instances-by-team/{node_info["team"]}')


def create_instance_info(node_info: Dict):
    with open(f'/tmp/instances-by-uuid/{node_info["uuid"]}', "w+") as f:
        f.write(json.dumps(node_info))

    with open(f'/tmp/instances-by-team/{node_info["team"]}', "w+") as f:
        f.write(json.dumps(node_info))


def really_kill_node(node_info: Dict):
    print(f"killing node {node_info['team']} {node_info['uuid']}")

    delete_instance_info(node_info)

    os.kill(node_info["pid"], signal.SIGTERM)


def kill_node(node_info: Dict):
    time.sleep(60 * 30)

    if not has_instance_by_uuid(node_info["uuid"]):
        return

    really_kill_node(node_info)


async def launch_node(team_id: str) -> Dict:
    port = str(random.randrange(30000, 60000))
    uuid = str(uuid4())
    seedMsgLine = "Seed to replicate this account sequence: "

    proc = await asyncio.create_subprocess_exec(
        f"starknet-devnet",
        f"--port={port}",
        "--accounts=2",
        stdout=asyncio.subprocess.PIPE,
    )

    client = FullNodeClient(f"http://127.0.0.1:{port}")
    stdout = await proc.stdout.readline()
    while seedMsgLine.encode() not in stdout:
        stdout += b"\n" + await proc.stdout.readline()
    while True:
        try:
            await client.get_block()
            break
        except Exception as e:
            print(e)
            pass
        time.sleep(0.1)
    accounts_re = re.findall(
        r"Account address.*?(0x[a-f0-9]+).*?Private key.*?(0x[a-f0-9]+).*?Public key.*?(0x[a-f0-9]+)",
        stdout.decode(),
        flags=re.DOTALL
    )
    accounts = []
    for account in accounts_re:
        accounts.append(
            {
                "address": account[0],
                "private_key": account[1],
                "public_key": account[2],
            }
        )
    seed_re = re.findall(
        f"{seedMsgLine}(.*)$",
        stdout.decode(),
    )
    node_info = {
        "port": port,
        "accounts": accounts,
        "pid": proc.pid,
        "uuid": uuid,
        "team": team_id,
        "seed": seed_re[0]
    }
    reaper = Thread(target=kill_node, args=(node_info,))
    reaper.start()
    return node_info


@app.route("/")
def index():
    return "sandbox is running!"


@app.route("/instance/new", methods=["POST"])
async def create():
    body = request.get_json()

    team_id = body["team_id"]

    if has_instance_by_team(team_id):
        print(f"refusing to run a new chain for team {team_id}")
        return {
            "ok": False,
            "error": "already_running",
            "message": "An instance is already running!",
        }

    print(f"launching node for team {team_id}")

    node_info = await launch_node(team_id)
    if node_info is None:
        print(f"failed to launch node for team {team_id}")
        return {
            "ok": False,
            "error": "error_starting_chain",
            "message": "An error occurred while starting the chain",
        }

    create_instance_info(node_info)

    print(
        f"launched node for team {team_id} (uuid={node_info['uuid']}, pid={node_info['pid']})"
    )

    return {
        **node_info,
        "ok": True
    }


@app.route("/instance/kill", methods=["POST"])
@cross_origin()
def kill():

    body = request.get_json()

    team_id = body["team_id"]

    if not has_instance_by_team(team_id):
        print(f"no instance to kill for team {team_id}")
        return {
            "ok": False,
            "error": "not_running",
            "message": "No instance is running!",
        }

    really_kill_node(get_instance_by_team(team_id))

    return {
        "ok": True,
        "message": "Instance killed",
    }


ALLOWED_NAMESPACES = ["starknet"]


@cross_origin()
def proxy_get(path):
    uuid = request.authorization.username
    if not has_instance_by_uuid(uuid):
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32602,
                "message": "invalid uuid specified",
            },
        }

    node_info = get_instance_by_uuid(uuid)
    url = f"http://127.0.0.1:{node_info['port']}/"
    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if key != "Host"},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
    )
    response = Response(resp.content, resp.status_code, resp.raw.headers.items())
    return response


@app.route("/<string:uuid>", methods=["POST"])
@cross_origin()
def proxy(uuid):
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

    node_info = get_instance_by_uuid(uuid)
    resp = requests.post(f"http://127.0.0.1:{node_info['port']}/", json=body)
    response = Response(resp.content, resp.status_code, resp.raw.headers.items())
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=HTTP_PORT)
