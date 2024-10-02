import json
from pathlib import Path
import toml
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account as StarknetAccount, KeyPair
from starknet_py.net.full_node_client import FullNodeClient

"""
UUID	4b3201f3-dd1a-4145-b71f-da7d4b33f6a9
RPC Endpoint	http://localhost:48334/4b3201f3-dd1a-4145-b71f-da7d4b33f6a9
Private Key	0x0000000000000000000000000000000000608ad76178c9f9b2a33c20ce4ec700
Setup Contract	0x68a1d74eab03cbeb9e37f5efb7456ebfd477d5e074e5a21a3f48fd3caaf30fd
Wallet	0x4dc74db3c5de182c05e98fabf270a9021e703d679ac9514664f5f21099d760d
"""
# StarkNet settings
RPC_URL = "http://localhost:48334/4b3201f3-dd1a-4145-b71f-da7d4b33f6a9"
PRIVKEY = "0x0000000000000000000000000000000000608ad76178c9f9b2a33c20ce4ec700"
SETUP_CONTRACT_ADDR = "0x68a1d74eab03cbeb9e37f5efb7456ebfd477d5e074e5a21a3f48fd3caaf30fd"
WALLET_ADDR = "0x4dc74db3c5de182c05e98fabf270a9021e703d679ac9514664f5f21099d760d"

SCARB_TOML = toml.load("./contracts/Scarb.toml")

TARGET_DEV = Path("./contracts/target/dev/")

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
    def __init__(self, class_name: str, abi=None) -> None:
        self.class_name = class_name

    async def abi(self, from_src=False):
        if from_src:
            name = SCARB_TOML["package"]["name"]
            klass = json.loads(TARGET_DEV.joinpath(f"{name}_{self.class_name}.contract_class.json").read_text())
            return klass['abi']
        else:
            klass = await Account().client.get_class_at(SETUP_CONTRACT_ADDR)
            return klass.parsed_abi

class BaseDeployedContract(Account, BaseContractProps):
    def __init__(self, addr, class_name, abi=None) -> None:
        BaseContractProps.__init__(self, class_name, abi)
        Account.__init__(self)
        self.address = addr
        self.contract = None
    async def __call__(self):
        await Account.__call__(self)
        self.contract = Contract(address=int(self.address, 16), abi=await self.abi(), provider=self.account_client)
        return self

class BaseUndeployedContract(Account, BaseContractProps):
    def __init__(self, class_name) -> None:
        BaseContractProps.__init__(self, class_name)
        Account.__init__(self)
        self.contract = None

    async def __call__(self):
        await Account.__call__(self)
        self.contract = Contract(abi=await self.abi(), client=self.account_client)
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

    async def is_solved(self):
        result = await self.contract.functions['is_solved'].call()
        print("is solved:", result)

    async def solve(self):
        result = await self.contract.functions['solve'].invoke_v1(max_fee=int(1e18))
        print("solve:", result)

async def main():
    setup = await SetupContract()()
    await setup.solve()
    await setup.is_solved()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
