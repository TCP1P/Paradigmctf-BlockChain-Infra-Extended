import json
from pathlib import Path
import toml
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account as StarknetAccount, KeyPair
from starknet_py.net.full_node_client import FullNodeClient

"""
UUID	3e4b1922-8339-4e3d-9c05-cf0320e84c47
RPC Endpoint	http://localhost:48334/3e4b1922-8339-4e3d-9c05-cf0320e84c47
Private Key	0x0000000000000000000000000000000008ecbaa9218bd9e55a7c925817a0124f
Setup Contract	0x77fb61096e2c5771c22b36dcb29aec076206c26204b60e2a5b8caa11babc793
Wallet	0x9ee8a5717da09d86eea2d6465e42783a32a1e357a614770fe31c47fe7358ec
"""
# StarkNet settings
RPC_URL = "http://localhost:48334/3e4b1922-8339-4e3d-9c05-cf0320e84c47"
PRIVKEY = "0x0000000000000000000000000000000008ecbaa9218bd9e55a7c925817a0124f"
SETUP_CONTRACT_ADDR = "0x77fb61096e2c5771c22b36dcb29aec076206c26204b60e2a5b8caa11babc793"
WALLET_ADDR = "0x9ee8a5717da09d86eea2d6465e42783a32a1e357a614770fe31c47fe7358ec"

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

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
