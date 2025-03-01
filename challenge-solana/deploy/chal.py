import asyncio
from pathlib import Path

import sandbox
import sandbox.solana_helper as helper
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair  # type: ignore
from interaction import setup

async def deploy_contract(client: AsyncClient, system_kp: Keypair, ctx_kp: Keypair, idl_path: Path, program_name: str, with_idl=True) -> str:
    """Deploy and initialize the Solana program without AnchorPy.
       Instead of using Anchor's IDL and RPC wrappers, we deploy the binary via CLI
       and then send an initialization transaction manually."""
    # Deploy the program binary.
    program_id = await helper.deploy_program(client, system_kp, program_name)
    print("program id:", program_id)
    if with_idl:
        await helper.initialize_idl(client, system_kp, idl_path, program_name)
    print("Succesfully initialize the program", await setup(client, system_kp, ctx_kp))
    return program_id

async def deploy(client: AsyncClient, system_kp: Keypair, player_kp: Keypair, ctx_kp: Keypair) -> str:
    """Orchestrate the full deployment process.
       Funds accounts in parallel then deploys and initializes the contract."""
    await asyncio.gather(
        helper.fund_account(client, system_kp, 5000),
        helper.fund_account(client, player_kp, 1)
    )
    return await deploy_contract(client, system_kp, ctx_kp, Path("target/idl/setup.json"), "setup")

app = sandbox.run_launcher(deploy)