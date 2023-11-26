import json
from web3 import Web3
from web3 import HTTPProvider
from subprocess import check_output

"""
https://github.com/foundry-rs/foundry

- Init new Project: forge init
- testing: forge test -vvv

Credentials:
UUID: 	38a19e78-394a-4748-8a4b-0d55e1f2e408
RPC Endpoint: 	http://localhost:8545/38a19e78-394a-4748-8a4b-0d55e1f2e408
Private Key: 	0x4aa563c1076b3d162f68814291ed83cb4e99765ad301f6bace11346327a7bc9d
Setup Contract: 	0x168A4D8facdC0613ce9Bf02c4E5321F3b14CdE43
"""

RPC_URL = "http://localhost:48334/38a19e78-394a-4748-8a4b-0d55e1f2e408"
PRIVKEY = "0x4aa563c1076b3d162f68814291ed83cb4e99765ad301f6bace11346327a7bc9d"
SETUP_CONTRACT_ADDR = "0x168A4D8facdC0613ce9Bf02c4E5321F3b14CdE43"

def get_abi(filename):
    # get abi "solc <filename> --abi"
    abi_str = check_output(['solc', filename, '--abi']).decode().split("Contract JSON ABI")[-1].strip()
    return json.loads(abi_str)

class Account:
    def __init__(self) -> None:
        self.w3 = Web3(HTTPProvider(RPC_URL))
        self.w3.eth.default_account = self.w3.eth.account.from_key(PRIVKEY).address
        self.account_address = self.w3.eth.default_account

    def get_balance(s, addr):
        print("balance:",s.w3.eth.get_balance(addr))


class BaseContract(Account):
    def __init__(self, addr, file, abi=None) -> None:
        super().__init__()
        self.file = file
        self.address = addr
        if abi:
            self.contract = self.w3.eth.contract(addr, abi=abi)
        else:
            self.contract = self.w3.eth.contract(addr, abi=self.get_abi())

    def get_abi(self):
        return get_abi(self.file)


class SetupContract(BaseContract):
    def __init__(self) -> None:
        super().__init__(
            addr=SETUP_CONTRACT_ADDR,
            file="Setup.sol",
            abi=[{"inputs":[{"internalType":"address","name":"player","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"PLAYER","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"isSolved","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"solve","outputs":[],"stateMutability":"nonpayable","type":"function"}]
        )
    def is_solved(s):
        result = s.contract.functions.isSolved().call()
        print("is solved:", result)

if __name__ == "__main__":
    setup = SetupContract()
    print(setup.contract.functions.solve().transact())
    setup.is_solved()
