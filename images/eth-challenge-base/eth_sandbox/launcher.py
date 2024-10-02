import json
import os
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional

import requests
from eth_account import Account
from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.types import TxReceipt
from flask import jsonify, session
import eth_sandbox.route as route

HTTP_PORT = os.getenv("HTTP_PORT", "8545")

FLAG = os.getenv("FLAG", "PCTF{placeholder}")

Account.enable_unaudited_hdwallet_features()

@dataclass
class Action:
    name: str
    handler: Callable[[], int]


def new_launch_instance_action(
    do_deploy: Callable[[Web3, str], str],
):
    def action():
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
        mnemonic = data["mnemonic"]

        deployer_acct : LocalAccount = Account.from_mnemonic(
            mnemonic, account_path=f"m/44'/60'/0'/0/0"
        )
        player_acct = Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/1")

        web3 = Web3(
            Web3.HTTPProvider(
                f"http://127.0.0.1:{data['port']}",
                request_kwargs={
                    "headers": {
                        "Content-Type": "application/json",
                    },
                },
            )
        )

        setup_addr = do_deploy(web3, deployer_acct.address, deployer_acct._private_key.hex(), player_acct.address)

        with open(f"/tmp/{ticket}", "w") as f:
            f.write(
                json.dumps(
                    {
                        "uuid": uuid,
                        "mnemonic": mnemonic,
                        "address": setup_addr,
                    }
                )
            )
            session["data"] = {
                "0": {"UUID": uuid},
                "1": {"RPC Endpoint": "{ORIGIN}/" + uuid},
                "2": {"Private Key": player_acct._private_key.hex()},
                "3": {"Setup Contract": setup_addr},
                "4": {"Wallet": player_acct._address},
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


def is_solved_checker(web3: Web3, addr: str) -> bool:
    result = web3.eth.call(
        {
            "to": addr,
            "data": Web3.keccak(text="isSolved()")[:4],
        }
    )
    return int(result.hex(), 16) == 1


def new_get_flag_action():
    ticket = session.get("ticket")
    if not ticket:
        raise Exception("please solve the challenge first")
    try:
        with open(f"/tmp/{ticket}", "r") as f:
            data = json.loads(f.read())
    except:
        raise Exception("bad ticket")

    web3 = Web3(Web3.HTTPProvider(f"http://127.0.0.1:{HTTP_PORT}/{data['uuid']}"))

    if not is_solved_checker(web3, data["address"]):
        raise Exception("are you sure you solved it?")

    return {"message": FLAG}


def handle_error(e):
    import traceback

    traceback.print_exc()

    response = jsonify(error=str(e))
    response.status_code = 400
    return response


def run_launcher(do_deploy: Callable[[Web3, str], str]):
    app = route.app
    app.get("/flag")(new_get_flag_action)
    app.get("/kill")(new_kill_instance_action)
    app.get("/launch")(new_launch_instance_action(do_deploy))
    app.errorhandler(Exception)(handle_error)
    return app
