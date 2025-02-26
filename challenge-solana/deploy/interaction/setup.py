from sandbox.solana_helper import execute_test, TempKeyfile
from solders.keypair import Keypair  # type: ignore
from solana.rpc.async_api import AsyncClient

async def setup(client: AsyncClient, system_kp: Keypair, ctx_kp: Keypair):
    async with TempKeyfile(system_kp) as keyfile:
        return await execute_test("setup", env={
            "solvedAccount": str(ctx_kp.to_bytes_array()),
            "ANCHOR_PROVIDER_URL": client._provider.endpoint_uri,
            "ANCHOR_WALLET": str(keyfile)
        })