import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey  # type: ignore
from solders.keypair import Keypair  # type: ignore
from anchorpy import Program, Provider, Wallet, Context
from solders.system_program import ID as SYS_PROGRAM_ID

PLAYER_KEYPAIR = "4ixKcq4BvkTbUiojSyQRm4wC1dSdQ6zeXwpuFbGCJVbwbk4VxRUVnUVHQu545YG7hgX5iEcaxRgoX5C572x1ZAkY"
CTX_PUBKEY = "7EBjs2pGtmpGK1gcGqzHb4bpeNSm4wmqMSkEvzy53Mbk"
PROGRAM_ID = "35qSrLjTWNtqytQKN487v5MzRQHnd1HaPqNsChzdiK5D"
RPC_URL = "http://localhost:48334/4215f49c-22ec-4649-92c3-48872079ca87"

async def main():
    client = AsyncClient(RPC_URL)
    sender = Keypair.from_base58_string(PLAYER_KEYPAIR)
    setup_program_id = Pubkey.from_string(PROGRAM_ID)
    ctx_pubkey = Pubkey.from_string(CTX_PUBKEY)
    provider = Provider(client, Wallet(sender))
    
    program = await Program.at(setup_program_id, provider)

    dat = await program.rpc['solve'](
        ctx=Context(
            accounts={
                "solved_account": ctx_pubkey,
                "user": provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID
            },
        ),
    )
    await client.confirm_transaction(dat)

    dat = await program.rpc['is_solved'](
        ctx=Context(
            accounts={
                "solved_account": ctx_pubkey,
                "user": provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID
            },
        ),
    )
    await client.confirm_transaction(dat)
    transaction_result = await client.get_transaction(dat)
    print(transaction_result.value.transaction.meta.return_data.data[0] == 1)

    # ac = await program.account['SolvedState'].fetch(ctx_pubkey)
    # print(ac)

if __name__ == "__main__":
    asyncio.run(main())
