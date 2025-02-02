import json
import os
import re
import asyncio
import tempfile
from pathlib import Path
from typing import Tuple
import toml

import sandbox
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey # type: ignore
from solders.keypair import Keypair # type: ignore
from anchorpy import Program, Provider, Wallet, Context
from solders.system_program import ID as SYS_PROGRAM_ID

# Constants
MAX_RETRIES = 20
DELAY = 1
CONTRACTS_DIR = Path("contracts")

class TempKeyfile:
    """Context manager for temporary keyfile handling"""
    def __init__(self, keypair: Keypair):
        self.keypair = keypair
        self.temp_file = None

    async def __aenter__(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        self.temp_file.write(str(self.keypair.to_json()))
        self.temp_file.close()
        return Path(self.temp_file.name)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.temp_file:
            os.remove(self.temp_file.name)

async def execute_command(*args: str, cwd: Path = None) -> Tuple[str, str]:
    """Execute shell command asynchronously with retries"""
    for _ in range(MAX_RETRIES):
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd) if cwd else None
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            return stdout.decode(), stderr.decode()
        print(stderr)
        await asyncio.sleep(DELAY)
    
    raise RuntimeError(f"Command failed after {MAX_RETRIES} attempts: {' '.join(args)}")

async def fund_account(client: AsyncClient, keypair: Keypair, amount: int):
    """Fund account using async subprocess"""
    await execute_command(
        "solana", "airdrop", str(amount),
        str(keypair.pubkey()), "--url", client._provider.endpoint_uri,
        "--commitment", "confirmed"
    )

def get_program_id_from_anchor_toml(contracts_dir: Path, program_name: str) -> str:
    """Extract program ID from Anchor.toml configuration"""
    anchor_toml_path = contracts_dir / "Anchor.toml"
    if not anchor_toml_path.exists():
        raise FileNotFoundError(f"Anchor.toml not found at {anchor_toml_path}")
    
    config = toml.load(anchor_toml_path)
    
    try:
        return config["programs"]["localnet"][program_name]
    except KeyError:
        raise KeyError(
            f"Program {program_name} not found in [programs.localnet] section of Anchor.toml"
        )

async def initialize_idl(client: AsyncClient, system_kp: Keypair, idl_path: Path, program_name: str):
    """Initialize IDL using program ID from Anchor.toml"""
    program_id = get_program_id_from_anchor_toml(CONTRACTS_DIR, program_name)
    
    async with TempKeyfile(system_kp) as keyfile:
        await execute_command(
            "anchor", "idl", "init", program_id,
            "--filepath", str(idl_path),
            "--provider.cluster", client._provider.endpoint_uri,
            "--provider.wallet", str(keyfile),
            cwd=CONTRACTS_DIR
        )

async def deploy_program(client: AsyncClient, system_kp: Keypair, program_name: str) -> str:
    """Deploy Solana program with proper async handling"""
    async with TempKeyfile(system_kp) as keyfile:
        stdout, _ = await execute_command(
            "anchor", "deploy", "--program-name", program_name,
            "--provider.cluster", client._provider.endpoint_uri,
            "--provider.wallet", str(keyfile),
            cwd=CONTRACTS_DIR
        )
        
    if match := re.search(r'Program Id: (\S+)', stdout):
        return match.group(1)
    raise RuntimeError("Failed to extract program ID from deployment output")

async def setup_program(client: AsyncClient, program_id: str, system_kp: Keypair) -> Program:
    """Initialize program instance with retries"""
    for _ in range(MAX_RETRIES):
        try:
            provider = Provider(client, Wallet(system_kp))
            return await Program.at(Pubkey.from_string(program_id), provider)
        except Exception as e:
            print(f"Program initialization failed: {e}")
            await asyncio.sleep(1)
    raise RuntimeError("Failed to initialize program after multiple attempts")

async def deploy_contract(client: AsyncClient, system_kp: Keypair, ctx_kp: Keypair, idl_path: Path, program_name: str) -> str:
    """Main deployment workflow"""
    # Deploy program
    await deploy_program(client, system_kp, program_name)
    
    # Get program ID from Anchor.toml
    program_id = get_program_id_from_anchor_toml(CONTRACTS_DIR, program_name)
    
    # Initialize IDL
    await initialize_idl(client, system_kp, idl_path, program_name)
    
    # Initialize program instance
    program = await setup_program(client, program_id, system_kp)
    provider = Provider(client, Wallet(system_kp))
    
    # Execute initialization transaction
    await program.rpc['initialize'](
        ctx=Context(
            accounts={
                "solved_account": ctx_kp.pubkey(),
                "user": provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID
            },
            signers=[ctx_kp]
        )
    )
    
    return program_id

async def deploy(client: AsyncClient, system_kp: Keypair, player_kp: Keypair, ctx_kp: Keypair) -> str:
    """Orchestrate full deployment process"""
    # Parallel account funding
    await asyncio.gather(
        fund_account(client, system_kp, 5000),
        fund_account(client, player_kp, 1)
    )
    
    return await deploy_contract(client, system_kp, ctx_kp, "target/idl/contract.json", "contracts")

app = sandbox.run_launcher(deploy)