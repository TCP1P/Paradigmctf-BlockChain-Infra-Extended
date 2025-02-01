import os
import subprocess

import sandbox # type: ignore
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey  # type: ignore
from solders.keypair import Keypair  # type: ignore
from anchorpy import Program, Provider, Wallet, Context
from solders.system_program import ID as SYS_PROGRAM_ID
from time import sleep
import re
import tempfile

def add_balance(client: AsyncClient, keypair: Keypair, amount: int):
    url = client._provider.endpoint_uri
    subprocess.run(
        ["solana", "airdrop", str(amount), str(keypair.pubkey()), "--url", url, "--commitment", "confirmed"],
        check=True,
        capture_output=True
    )

def init_idl(client: AsyncClient, system_kp: Keypair, program_id: str):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write(str(system_kp.to_json()))
    while True:
        res2 = subprocess.run(
            ["anchor", "idl", "init", str(program_id), "--filepath", "./target/idl/contract.json","--provider.cluster", client._provider.endpoint_uri, "--provider.wallet", temp_file.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="contracts/"
        )
        if res2.stderr:
            print(res2.stderr)
            sleep(1)
        else:
            break
    print(res2.stdout)
    os.remove(temp_file.name)

def deploy_program(client: AsyncClient, system_kp: Keypair, program_name: str):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write(str(system_kp.to_json()))
    res = subprocess.run(
        ["anchor", "deploy", "--program-name", program_name, "--provider.cluster", client._provider.endpoint_uri, "--provider.wallet", temp_file.name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="contracts/"
    )
    os.remove(temp_file.name)
    if res.stderr:
        raise Exception(res.stderr)
    else:
        print(res.stdout)
        program_id = re.findall(r'Program Id: (.*)', res.stdout.decode())[0].strip()
        return program_id


async def deploy_contract(client: AsyncClient, system_kp: Keypair, ctx_kp: Keypair):
    program_id = deploy_program(client, system_kp, "contracts")
    program_pubkey = Pubkey.from_string(program_id)
    provider = Provider(client, Wallet(system_kp))

    init_idl(client, system_kp, program_id)

    while True:
        try:
            program = await Program.at(program_pubkey, provider)
            print("successfully generate program")
            break
        except Exception as e:
            print(e)
            sleep(1)
            pass
    await program.rpc['initialize'](
        ctx=Context(
            accounts={
                "solved_account": ctx_kp.pubkey(),  # New account to be initialized.
                "user": provider.wallet.public_key,     # Payer and authority.
                "system_program": SYS_PROGRAM_ID         # System program for account creation.
            },
            signers=[ctx_kp]  # Include new account to sign.
        ),
    )
    
    return program_id

async def deploy(client: AsyncClient, system_kp: Keypair, player_kp: Keypair, ctx_kp: Keypair) -> str:
    add_balance(client, system_kp, 5000)
    add_balance(client, player_kp, 1)
    return await deploy_contract(client, system_kp, ctx_kp)

app = sandbox.run_launcher(deploy)
