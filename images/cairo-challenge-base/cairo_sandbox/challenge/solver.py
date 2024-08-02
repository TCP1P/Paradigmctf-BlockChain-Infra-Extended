import json
from pathlib import Path
import toml
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account as StarknetAccount, KeyPair
from starknet_py.net.full_node_client import FullNodeClient

# StarkNet settings
RPC_URL = "http://127.0.0.1:5000/ace6fd2b-1af9-470c-a594-9023aaf00ed9"
PRIVKEY = "0x7ae88df1a5281497a5d767c1d256c403"
SETUP_CONTRACT_ADDR = "0x7a01337b9f8b038a62f62830e83acedae0a41ce10da69824533b378283beea1"
WALLET_ADDR = "0x5d6a84c71bdab35dcdc7a75fc2923790f0986edaa506c1e885905f658b50ead"

SCARB_TOML = toml.load("./Scarb.toml")

TARGET_DEV = Path("./target/dev/")

class Account:
    def __init__(self) -> None:
        self.client = FullNodeClient(RPC_URL)
        self.key_pair = KeyPair.from_private_key(int(PRIVKEY, 16))
        self.account_client = None

    async def __call__(self):
        self.account_client = StarknetAccount(
            client=self.client,
            key_pair=self.key_pair,
            address=WALLET_ADDR,
            chain=await self.client.get_chain_id()
        )
        return self

class BaseContractProps:
    def __init__(self, class_name: str) -> None:
        self.class_name = class_name

    @property
    def abi(self):
        name = SCARB_TOML["package"]["name"]
        klass = json.loads(TARGET_DEV.joinpath(f"{name}_{self.class_name}.contract_class.json").read_text())
        return klass['abi']

class BaseDeployedContract(Account, BaseContractProps):
    def __init__(self, addr, class_name) -> None:
        BaseContractProps.__init__(self, class_name)
        Account.__init__(self)
        self.address = addr
        self.contract = None

    async def __call__(self):
        await Account.__call__(self)
        self.contract = Contract(address=int(self.address, 16), abi=self.abi, provider=self.account_client)
        return self

class BaseUndeployedContract(Account, BaseContractProps):
    def __init__(self, class_name) -> None:
        BaseContractProps.__init__(self, class_name)
        Account.__init__(self)
        self.contract = None

    async def __call__(self):
        await Account.__call__(self)
        self.contract = Contract(abi=self.abi, client=self.account_client)
        return self

    async def deploy(self, *args):
        deploy_result = await self.contract.deploy_contract_v1(*args)
        await deploy_result.wait_for_acceptance()
        return BaseDeployedContract(deploy_result.deployed_contract.address, self.class_name)

class SetupContract(BaseDeployedContract):
    def __init__(self) -> None:
        super().__init__(
            addr=SETUP_CONTRACT_ADDR,
            class_name="setup",
        )

    async def __call__(self):
        await super().__call__()
        return self

    async def is_solved(self):
        result = await self.contract.functions['is_solved'].call()
        print("is solved:", result)

    async def solve(self):
        result = await self.contract.functions['solve'].invoke_v1(max_fee=int(1e18))
        print("solve:", result)

async def main():
    setup = await SetupContract()()
    await setup.solve()
    print(await setup.is_solved())
    # hack = HackContract()
    # await hack()
    # hack_deployed = await hack.deploy(await setup.target)
    # await hack_deployed.call_function("hack")
    # await setup.is_solved()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
