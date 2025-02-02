import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey  # type: ignore
from solders.keypair import Keypair  # type: ignore
from anchorpy import Program, Provider, Wallet, Context
from solders.system_program import ID as SYS_PROGRAM_ID

PLAYER_KEYPAIR = "4CWJLhmCCqQT53qHijMGHkUXLTv9LeLkeTno9jguuaZCzjc6gEHhuUr4FtsvEvAdTYKaccXKLTv1n4nSuKGrYgFH"
CTX_PUBKEY = "CkPvKMTjUkDwpPLYUZX7KAjUAGAfqg6EeGv2Y7HX6CYR"
PROGRAM_ID = "35qSrLjTWNtqytQKN487v5MzRQHnd1HaPqNsChzdiK5D"
RPC_URL = "http://localhost:48334/b29ff677-a76b-4d95-82a3-8c18bcb0f79b"

async def main():
    client = AsyncClient(RPC_URL)
    sender = Keypair.from_base58_string(PLAYER_KEYPAIR)
    setup_program_id = Pubkey.from_string(PROGRAM_ID)
    ctx_pubkey = Pubkey.from_string(CTX_PUBKEY)
    provider = Provider(client, Wallet(sender))
    
    program = await Program.at(setup_program_id, provider)

    solve_tx = await program.rpc['solve'](
        ctx=Context(
            accounts={
                "solved_account": ctx_pubkey,
                "user": provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID
            },
        ),
    )

    is_solved_tx = await program.rpc['is_solved'](
        ctx=Context(
            accounts={
                "solved_account": ctx_pubkey,
                "user": provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID
            },
        ),
    )
    await asyncio.gather(
        client.confirm_transaction(solve_tx),
        client.confirm_transaction(is_solved_tx),
    )
    transaction_result = await client.get_transaction(is_solved_tx)
    print(transaction_result.value.transaction.meta.return_data.data[0] == 1)

    # ac = await program.account['SolvedState'].fetch(ctx_pubkey)
    # print(ac)

if __name__ == "__main__":
    asyncio.run(main())
