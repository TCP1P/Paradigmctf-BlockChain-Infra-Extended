import json
from web3 import Web3
from web3 import HTTPProvider
from subprocess import check_output

"""
https://github.com/foundry-rs/foundry

- Init new Project: forge init
- testing: forge test -vvv

Credentials:

UUID	eca06b1a-8bd1-4ee1-847d-38fee12e57c5
RPC Endpoint	http://localhost:48334/eca06b1a-8bd1-4ee1-847d-38fee12e57c5
Private Key	0x6b9884607deeb3b03e224c0c6b49d2ce2682ce5cbea8919648b9e7d7dc28d564
Setup Contract	0xD66aAe948B365EE0230A91119e04d7FD11A22d7f
Wallet	0xbf758881E6132A53BbED8b2E0Bd2C1AFb15689b2

"""

RPC_URL = "http://localhost:48334/e1d665fb-268b-4f8d-bb2d-6118df6c9fe9"
PRIVKEY = "0x00000000000000000000000000000000c4433338000a70fd6b4fdd6d7011abd7"
SETUP_CONTRACT_ADDR = "0x24f4023561d34c52b4256d92996735e5789925e4074aaecb3a1fa011b838128"
WALLET_ADDR = "0x06d3f98fe78b115251865a6e643499cc8ab28553c181ab732bcb77126e0e2e07"


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
