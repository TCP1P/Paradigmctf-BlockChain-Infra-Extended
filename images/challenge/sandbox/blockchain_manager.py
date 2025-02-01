import os
import random
import subprocess
import signal
import json
import time
from threading import Thread
from typing import Callable, List, Literal
from uuid import uuid4
import re
import asyncio

from .type import AccountInfo, NodeInfo
import os
import random
import subprocess
import signal
import sys
import json
import time
from threading import Thread
from uuid import uuid4
from base58 import b58encode


import asyncio
from solders.pubkey import Pubkey  # type: ignore
from solders.keypair import Keypair  # type: ignore
from anchorpy import Program, Provider, Wallet, Context
from solders.system_program import ID as SYS_PROGRAM_ID

from web3 import Web3

BLOCKCHAIN_TYPE = os.getenv("BLOCKCHAIN_TYPE", False)
print("Starting Blockchain manager...")
if BLOCKCHAIN_TYPE == False:
    print("BLOCKCHAIN_TYPE isn't defined")
    sys.exit(1)

from starknet_py.contract import Contract as cairoContract
from starknet_py.net.account.account import Account as cairoAccount, KeyPair as cairoKeyPair
from starknet_py.net.full_node_client import FullNodeClient as cairoFullNodeClient
from eth_account import Account as ethAccount
from eth_account.hdaccount import generate_mnemonic
from eth_account.signers.local import LocalAccount as ethLocalAccount
from solana.rpc.async_api import AsyncClient as SolanaClient

ethAccount.enable_unaudited_hdwallet_features()

try:
    os.mkdir("/tmp/instances-by-team")
    os.mkdir("/tmp/instances-by-uuid")
except:
    pass


def has_instance_by_uuid(uuid: str) -> bool:
    return os.path.exists(f"/tmp/instances-by-uuid/{uuid}")


def has_instance_by_team(team: str) -> bool:
    return os.path.exists(f"/tmp/instances-by-team/{team}")


def get_instance_by_uuid(uuid: str):
    with open(f"/tmp/instances-by-uuid/{uuid}", "r") as f:
        return NodeInfo(**json.loads(f.read()))


def get_instance_by_team(team: str):
    with open(f"/tmp/instances-by-team/{team}", "r") as f:
        return NodeInfo(**json.loads(f.read()))


def delete_instance_info(node_info: NodeInfo):
    os.remove(f'/tmp/instances-by-uuid/{node_info.uuid}')
    os.remove(f'/tmp/instances-by-team/{node_info.team}')
    try:
        os.rmdir(f"/home/ctf/{node_info.uuid}")
    except:
        pass


def create_instance_info(node_info: NodeInfo):
    with open(f'/tmp/instances-by-uuid/{node_info.uuid}', "w") as f:
        f.write(json.dumps(node_info.to_dict()))

    with open(f'/tmp/instances-by-team/{node_info.team}', "w") as f:
        f.write(json.dumps(node_info.to_dict()))


def really_kill_node(node_info: NodeInfo):
    print(f"killing node {node_info.team} {node_info.uuid}")
    delete_instance_info(node_info)
    os.kill(node_info.pid, signal.SIGTERM)


def kill_node(node_info: NodeInfo):
    time.sleep(60 * 30)

    if not has_instance_by_uuid(node_info.uuid):
        return False

    really_kill_node(node_info)
    return True


async def launch_node_cairo(team_id: str) -> (NodeInfo | None):
    if not team_id:
        return None
    port = str(random.randrange(30000, 60000))
    uuid = str(uuid4())
    seedMsgLine = "Seed to replicate this account sequence: "

    proc = await asyncio.create_subprocess_exec(
        f"starknet-devnet",
        f"--port={port}",
        "--accounts=2",
        stdout=asyncio.subprocess.PIPE,
    )

    client = cairoFullNodeClient(f"http://127.0.0.1:{port}")
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
    accounts: List[AccountInfo] = []
    for account in accounts_re:
        accounts.append(AccountInfo(
            address=account[0],
            private_key=account[1],
            public_key=account[2]
        ))
    seed_re = re.findall(
        f"{seedMsgLine}(.*)$",
        stdout.decode(),
    )
    node_info: NodeInfo = NodeInfo(port=port, accounts=accounts, pid=proc.pid, uuid=uuid, team=team_id, seed=seed_re[0])
    reaper = Thread(target=kill_node, args=(node_info,))
    reaper.start()
    return node_info

def launch_node_eth(team_id: str):
    port = random.randrange(30000, 60000)
    mnemonic = generate_mnemonic(12, "english")
    uuid = str(uuid4())

    proc = subprocess.Popen(
        args=[
            "anvil",
            "--accounts",
            "2",  # first account is the deployer, second account is for the user
            "--balance",
            "5000",
            "--mnemonic",
            mnemonic,
            "--port",
            str(port),
            # "--fork-url",
            # ETH_RPC_URL,
            "--block-base-fee-per-gas",
            "0",
        ],
    )

    web3 = Web3(Web3.HTTPProvider(f"http://127.0.0.1:{port}"))
    while True:
        print("Waiting for the foundry to properly start...", file=sys.stderr)
        if proc.poll() is not None:
            return None
        if web3.is_connected():
            break
        time.sleep(0.1)

    deployer_acct : ethLocalAccount = ethAccount.from_mnemonic(
        mnemonic, account_path=f"m/44'/60'/0'/0/0"
    )
    player_acct : ethLocalAccount = ethAccount.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/1")

    accounts: List[AccountInfo] = [
        AccountInfo(address=deployer_acct.address, private_key=deployer_acct.key.hex(), public_key=deployer_acct._address),
        AccountInfo(address=player_acct.address, private_key=player_acct.key.hex(), public_key=player_acct._address)
    ] 

    node_info = NodeInfo(
        port=port,
        accounts=accounts,
        pid=proc.pid,
        uuid=uuid,
        team=team_id,
        seed=mnemonic
    )

    reaper = Thread(target=kill_node, args=(node_info,))
    reaper.start()
    return node_info

def launch_node_solana(team_id: str):
    port = random.randrange(30000, 60000)
    uuid = str(uuid4())

    # Start Solana test validator
    proc = subprocess.Popen(
        ["solana-test-validator", "--rpc-port", str(port), "--quiet", "--ledger", uuid],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for validator to be ready
    while True:
        try:
            check_proc = subprocess.run(
                ["solana", "cluster-version", "--url", f"http://localhost:{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if check_proc.returncode == 0:
                break
        except subprocess.TimeoutExpired:
            continue
        time.sleep(0.5)

    # Generate keypairs
    system_keypair = Keypair()
    player_keypair = Keypair()
    ctx_keypair = Keypair()

    accounts = [
        AccountInfo(
            address=str(system_keypair.pubkey()),
            private_key=b58encode(bytes(system_keypair)).decode(),
            public_key=str(system_keypair.pubkey())
        ),
        AccountInfo(
            address=str(player_keypair.pubkey()),
            private_key=b58encode(bytes(player_keypair)).decode(),
            public_key=str(player_keypair.pubkey())
        ),
        AccountInfo(
            address=str(ctx_keypair.pubkey()),
            private_key=b58encode(bytes(ctx_keypair)).decode(),
            public_key=str(ctx_keypair.pubkey())
        ),
    ]

    node_info = NodeInfo(
        port=port,
        accounts=accounts,
        pid=proc.pid,
        uuid=uuid,
        team=team_id,
        seed=None,
        contract_addr=None
    )

    reaper = Thread(target=kill_node, args=(node_info,))
    reaper.start()
    return node_info
    
class BlockchainManager:
    def __init__(self, blockchain_type: Literal["cairo", "eth", "solana"]):
        self.blockchain_type = blockchain_type
        if blockchain_type == "cairo":
            from starknet_py.net.full_node_client import FullNodeClient
            self.client = FullNodeClient("http://127.0.0.1:8545")
        elif blockchain_type == "eth":
            from web3 import Web3
            self.client = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

    async def start_instance(
            self, 
            team_id: str, 
            do_deploy: Callable[[cairoFullNodeClient, cairoAccount, cairoAccount], str] 
            | Callable[[Web3, str], str] 
            | Callable[[SolanaClient, Keypair, Keypair, Keypair], str]
        ):
        if has_instance_by_team(team_id):
            raise Exception("instace already exist, please kill it before start it again")
        if self.blockchain_type == "cairo":
            team_node = await launch_node_cairo(team_id)
            if team_node:
                client = cairoFullNodeClient(f"http://127.0.0.1:{team_node.port}")
                player_private_key = team_node.accounts[0].private_key
                player_address = team_node.accounts[0].address
                player_account = cairoAccount(
                    client=client,
                    address=player_address,
                    key_pair=cairoKeyPair.from_private_key(player_private_key),
                    chain=await client.get_chain_id()
                )
                system_private_key = team_node.accounts[1].private_key
                system_address = team_node.accounts[1].address
                system_account = cairoAccount(
                    client=client,
                    address=system_address,
                    key_pair=cairoKeyPair.from_private_key(system_private_key),
                    chain=await client.get_chain_id()
                )
                contract_addr = hex(await do_deploy(client, system_account, player_account))
                team_node.contract_addr = contract_addr
                create_instance_info(team_node)
                return team_node
        elif self.blockchain_type == "eth":
            team_node = launch_node_eth(team_id)
            if team_node:
                deployer_acct : ethLocalAccount = ethAccount.from_mnemonic(
                    team_node.seed, account_path=f"m/44'/60'/0'/0/0"
                )
                player_acct = ethAccount.from_mnemonic(team_node.seed, account_path=f"m/44'/60'/0'/0/1")

                web3 = Web3(
                    Web3.HTTPProvider(
                        f"http://127.0.0.1:{team_node.port}",
                        request_kwargs={
                            "headers": {
                                "Content-Type": "application/json",
                            },
                        },
                    )
                )

                setup_addr = await do_deploy(web3, deployer_acct.address, deployer_acct._private_key.hex(), player_acct.address)
                team_node.contract_addr = setup_addr
                create_instance_info(team_node)
                return team_node
        elif self.blockchain_type == "solana":
            team_node = launch_node_solana(team_id)
            if team_node:
                client = SolanaClient(f"http://localhost:{team_node.port}")
                system_kp = Keypair.from_base58_string(team_node.accounts[0].private_key)
                player_kp = Keypair.from_base58_string(team_node.accounts[1].private_key)
                ctx_kp = Keypair.from_base58_string(team_node.accounts[2].private_key)
                
                # Deploy contract/program
                contract_addr = await do_deploy(client, system_kp, player_kp, ctx_kp)
                team_node.contract_addr = contract_addr
                create_instance_info(team_node)
                return team_node
        raise Exception("failed creating an instace")
    def kill_instance(self, team_id: str):
        if has_instance_by_team(team_id):
            return really_kill_node(get_instance_by_team(team_id))
        raise Exception("instance doesn't exist")
    
    async def is_solved(self, team_id):
        if not has_instance_by_team(team_id):
            raise Exception("please launch your instance first")
        data = get_instance_by_team(team_id)
        if self.blockchain_type == "cairo":
            client = cairoFullNodeClient(f"http://127.0.0.1:{data.port}")
            system_address = data.accounts[0].address
            system_private_key = data.accounts[0].private_key
            # https://github.com/Shard-Labs/starknet-devnet/blob/a5c53a52dcf453603814deedb5091ab8c231c3bd/starknet_devnet/account.py#L35
            system_client = cairoAccount(
                client=client,
                address=system_address,
                key_pair=cairoKeyPair.from_private_key(system_private_key),
                chain=await client.get_chain_id()
            )
            contract = await cairoContract.from_address(
                int(data.contract_addr, 16), system_client
            )
            result = await contract.functions.get("is_solved").call()
            if isinstance(result, bool):
                return result
            if isinstance(result, tuple) or isinstance(result, list):
                return result[0]
        elif self.blockchain_type == "eth":
            web3 = Web3(Web3.HTTPProvider(f"http://127.0.0.1:{data.port}"))
            result = web3.eth.call(
                {
                    "to": data.contract_addr,
                    "data": Web3.keccak(text="isSolved()")[:4],
                }
            )
            return int(result.hex(), 16) == 1
        elif self.blockchain_type == "solana":
            team_node = get_instance_by_team(team_id)
            client = SolanaClient(f"http://localhost:{team_node.port}")
            system_acc = Keypair.from_base58_string(team_node.accounts[0].private_key)
            provider = Provider(client, Wallet(system_acc))
            program = await Program.at(team_node.contract_addr, provider)
            signature = await program.rpc['is_solved'](ctx=Context(
                accounts={
                    "solved_account": Pubkey.from_string(team_node.accounts[2].public_key),
                    "user": provider.wallet.public_key,
                    "system_program": SYS_PROGRAM_ID
                }
            ))
            await client.confirm_transaction(signature)
            transaction_result = await client.get_transaction(signature)
            return transaction_result.value.transaction.meta.return_data.data[0] == 1



BM = BlockchainManager(BLOCKCHAIN_TYPE)
