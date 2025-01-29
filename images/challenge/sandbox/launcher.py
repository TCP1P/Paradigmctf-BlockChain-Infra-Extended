import os
from typing import Callable

from flask import jsonify, session
from .route import app

from .blockchain_manager import *

HTTP_PORT = os.getenv("HTTP_PORT", "8545")
LAUNCHER_PORT = os.getenv("LAUNCHER_PORT", "8546")
FLAG = os.getenv("FLAG", "PCTF{placeholder}")

def new_launch_instance_action(
    do_deploy: Callable[[cairoFullNodeClient, cairoAccount, cairoAccount], str] | Callable[[Web3, str], str],
):
    async def action():
        ticket = session.get("ticket")
        if not ticket:
            raise Exception("please solve the challenge first")
        data = await BM.start_instance(ticket, do_deploy)
        player_private_key = data.accounts[1].private_key
        player_address = data.accounts[1].address
        contract_addr = data.contract_addr
        session["data"] = {
            "0": {"UUID": data.uuid},
            "1": {"RPC_URL": "{ORIGIN}/"+data.uuid},
            "2": {"PRIVKEY": player_private_key},
            "3": {"SETUP_CONTRACT_ADDR": contract_addr},
            "4": {"WALLET_ADDR": player_address},
            "message": "your private blockchain has been deployed, it will automatically terminate in 30 minutes",
        }
        return session["data"]

    return action

def new_kill_instance_action():
    ticket = session.get("ticket")
    if not ticket:
        raise Exception("please solve the challenge first")
    BM.kill_instance(ticket)
    return jsonify({"message": "Successfully killing the terminator"})


async def new_get_flag_action():
    ticket = session.get("ticket")
    if not ticket:
        raise Exception("please solve the challenge first")
    if not await BM.is_solved(ticket):
        raise Exception("are you sure you solved it?")
    return jsonify({"message": FLAG})


def handle_error(e):
    import traceback
    traceback.print_exc()
    response = jsonify(error=str(e))
    response.status_code = 400
    return response

def run_launcher(do_deploy: Callable[[cairoFullNodeClient, str], str]):
    app.get("/flag")(new_get_flag_action)
    app.get("/kill")(new_kill_instance_action)
    app.get("/launch")(new_launch_instance_action(do_deploy))
    app.errorhandler(Exception)(handle_error)
    return app
