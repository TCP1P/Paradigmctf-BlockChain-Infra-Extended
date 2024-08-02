#[starknet::interface]
pub trait IContract<TContractState> {
    fn solve(ref self: TContractState);
    fn is_solved(ref self: TContractState) -> bool;
}

#[starknet::contract]
pub mod setup {
    #[storage]
    struct Storage {
        solved: bool,
    }

    #[abi(embed_v0)]
    impl Setup of super::IContract<ContractState> {
        fn solve(ref self: ContractState) {
            self.solved.write(true);
        }

        fn is_solved(ref self: ContractState) -> bool {
            return self.solved.read();
        }
    }
}

#[cfg(test)]
mod tests {
    use challenge::setup::IContract;
    use super::setup;

    #[test]
    fn it_works() {
        let mut contract = setup::contract_state_for_testing();
        contract.solve();
        assert!(contract.is_solved());
        return;
    }
}
