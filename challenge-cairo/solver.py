import json
from pathlib import Path
from subprocess import check_output
import tempfile
import toml
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account as StarknetAccount, KeyPair
from starknet_py.net.full_node_client import FullNodeClient

"""
UUID = "9b74b15f-f109-4c1f-9e85-5675ed1ea703"
RPC Endpoint = "http://localhost:48334/9b74b15f-f109-4c1f-9e85-5675ed1ea703"
Private Key = "0x00000000000000000000000000000000453ee795f782b4692444da67f531bb71"
Setup Contract = "0x13562b0760b37b7f9e0e8e029ca47e9344605285c00f7a2de7e861d6c58054d"
Wallet = "0x06402e815043798d6b10aa16a688680d710b6f4c501140c8088679975d7e6654"
"""
# StarkNet settings
RPC_URL = "http://localhost:48334/6e15a814-90fe-468b-9db6-87ac07c06b2d"
PRIVKEY = "0x00000000000000000000000000000000334cf6cbd8093929d8b2efea7e3ea446"
SETUP_CONTRACT_ADDR = "0x26c8af8df97942429a6b1a90899559226ed432d3656225b99f58f81910dc4d6"
WALLET_ADDR = "0x020be3a497fbf41c5296bee784de27bcd16beddfd274685e75482624d282a9b8"

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

    async def disass(self):
        klass = await self.client.get_class_at(SETUP_CONTRACT_ADDR)

        # Convert program and entry points to hex
        for i in range(len(klass.sierra_program)):
            klass.sierra_program[i] = hex(klass.sierra_program[i])

        for i in range(len(klass.entry_points_by_type.external)):
            klass.entry_points_by_type.external[i].selector = hex(klass.entry_points_by_type.external[i].selector)
            klass.entry_points_by_type.external[i] = klass.entry_points_by_type.external[i].__dict__

        klass.entry_points_by_type.__dict__['EXTERNAL'] = klass.entry_points_by_type.external
        klass.entry_points_by_type.__dict__['L1_HANDLER'] = klass.entry_points_by_type.l1_handler
        klass.entry_points_by_type.__dict__['CONSTRUCTOR'] = klass.entry_points_by_type.constructor

        # Use a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            sierra_path = f"{temp_dir}/sierra.json"
            compiled_sierra_path = f"{temp_dir}/compiled_sierra.json"

            # Write the sierra.json file
            with open(sierra_path, "w") as f:
                f.write(json.dumps({
                    "sierra_program": klass.sierra_program,
                    "contract_class_version": klass.contract_class_version,
                    "entry_points_by_type": klass.entry_points_by_type.__dict__,
                    "EXTERNAL": klass.entry_points_by_type.external
                }))

            # Compile the sierra.json file
            with open(compiled_sierra_path, "wb") as f:
                f.write(check_output(["starknet-sierra-compile", sierra_path]))

            # Use Thoth to process the compiled file
            return check_output(["thoth", "local", compiled_sierra_path, "-b"]).decode()

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
