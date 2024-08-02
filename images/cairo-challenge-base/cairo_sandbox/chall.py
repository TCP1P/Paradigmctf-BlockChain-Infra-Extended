import launcher

from pathlib import Path

from starknet_py.net.account.account import Account
from starknet_py.contract import Contract, DeployResult
from starknet_py.net.full_node_client import FullNodeClient


async def deploy(
    client: FullNodeClient, system_account: Account, player_account: Account
) -> str:
    declare_result = await Contract.declare_v2(
        account=system_account,
        compiled_contract=Path(
            "challenge/target/dev/challenge_setup.contract_class.json"
        ).read_text(),
        max_fee=int(1e18),
        compiled_contract_casm=Path(
            "challenge/target/dev/challenge_setup.compiled_contract_class.json"
        ).read_text(),
    )

    await declare_result.wait_for_acceptance()
    setup_deployment: DeployResult = await declare_result.deploy_v1(max_fee=int(1e18))

    print("[+] initializing contracts")
    return setup_deployment.deployed_contract.address


app = launcher.run_launcher(deploy)
app.run("0.0.0.0", 5000)
