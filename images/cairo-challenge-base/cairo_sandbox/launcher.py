import json
import os
import random
import string
from dataclasses import dataclass
from typing import Callable

import requests
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account, KeyPair

from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.client import Client
from starknet_py.hash.utils import private_to_stark_key
from starknet_py.hash.address import compute_address
from flask import jsonify, session
try:
    import cairo_sandbox.route as route
except:
    import route

HTTP_PORT = os.getenv("HTTP_PORT", "8545")
LAUNCHER_PORT = os.getenv("LAUNCHER_PORT", "8546")

FLAG = os.getenv("FLAG", "PCTF{placeholder}")

def new_launch_instance_action(
    do_deploy: Callable[[FullNodeClient, Account, Account], str],
):
    async def action():
        ticket = session.get("ticket")
        if not ticket:
            raise Exception("please solve the challenge first")

        data = requests.post(
            f"http://127.0.0.1:{HTTP_PORT}/instance/new",
            headers={
                "Content-Type": "application/json",
            },
            data=json.dumps(
                {
                    "team_id": ticket,
                }
            ),
        ).json()

        if data["ok"] == False:
            raise Exception(data["message"])

        uuid = data["uuid"]
        accounts = data["accounts"]
        client = FullNodeClient(f"http://127.0.0.1:{data['port']}")

        player_private_key = accounts[0]["private_key"]
        player_address = accounts[0]["address"]

        player_account = Account(
            client=client,
            address=player_address,
            key_pair=KeyPair.from_private_key(player_private_key),
            chain=await client.get_chain_id()
        )


        system_private_key = accounts[1]["private_key"]
        system_address = accounts[1]["address"]

        system_account = Account(
            client=client,
            address=system_address,
            key_pair=KeyPair.from_private_key(system_private_key),
            chain=await client.get_chain_id()
        )

        contract_addr = hex(await do_deploy(client, system_account, player_account))

        with open(f"/tmp/{ticket}", "w") as f:
            f.write(
                json.dumps(
                    {
                        "uuid": uuid,
                        "address": contract_addr,
                        "accounts": accounts
                    }
                )
            )
            session["data"] = {
                "0": {"UUID": uuid},
                "1": {"RPC Endpoint": "{ORIGIN}/"+uuid},
                "2": {"Private Key": player_private_key},
                "3": {"Setup Contract": contract_addr},
                "4": {"Wallet": player_address},
                "message": "your private blockchain has been deployed, it will automatically terminate in 30 minutes",
            }
        return session["data"]

    return action


def new_kill_instance_action():
    ticket = session.get("ticket")
    if not ticket:
        raise Exception("please solve the challenge first")

    data = requests.post(
        f"http://127.0.0.1:{HTTP_PORT}/instance/kill",
        headers={
            "Content-Type": "application/json",
        },
        data=json.dumps(
            {
                "team_id": ticket,
            }
        ),
    ).json()

    return {"message": data["message"]}


async def is_solved_checker(contract: Contract):
    result = await contract.functions.get("is_solved").call()
    print("result:", result)
    if isinstance(result, bool):
        return result
    if isinstance(result, tuple) or isinstance(result, list):
        return result[0]


async def new_get_flag_action():
    ticket = session.get("ticket")
    if not ticket:
        raise Exception("please solve the challenge first")
    try:
        with open(f"/tmp/{ticket}", "r") as f:
            data = json.loads(f.read())
    except:
        raise Exception("bad ticket")

    client = FullNodeClient(f"http://127.0.0.1:{HTTP_PORT}/{data['uuid']}")

    system_address = data['accounts'][0]['address']
    system_private_key = data['accounts'][0]['private_key']
    # https://github.com/Shard-Labs/starknet-devnet/blob/a5c53a52dcf453603814deedb5091ab8c231c3bd/starknet_devnet/account.py#L35
    system_client = Account(
        client=client,
        address=system_address,
        key_pair=KeyPair.from_private_key(system_private_key),
        chain=await client.get_chain_id()
    )
    contract = await Contract.from_address(
        int(data["address"], 16), system_client
    )

    if not is_solved_checker(contract):
        raise Exception("are you sure you solved it?")

    return {"message": FLAG}


def handle_error(e):
    import traceback

    traceback.print_exc()

    response = jsonify(error=str(e))
    response.status_code = 400
    return response


def run_launcher(do_deploy: Callable[[FullNodeClient, str], str]):
    app = route.app
    app.get("/flag")(new_get_flag_action)
    app.get("/kill")(new_kill_instance_action)
    app.get("/launch")(new_launch_instance_action(do_deploy))
    app.errorhandler(Exception)(handle_error)
    return app
