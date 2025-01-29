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

UUID = "56ba8f72-0fd5-4e18-8039-fdb36c25aebc"
RPC_URL = "http://localhost:48334/56ba8f72-0fd5-4e18-8039-fdb36c25aebc"
PRIVKEY = "0x92f51b2e71ee409a31c908a992435d708b2d3a1d5d759be7cb60e656c4ad0d9f"
SETUP_CONTRACT_ADDR = "0x2aEDD9056e0ef2D3BBAe6F1C21B7e30723C424aD"
WALLET_ADDR = "0xBE639691Ff0e7bE6dcD97E90CfB633d637d26ECc"

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
