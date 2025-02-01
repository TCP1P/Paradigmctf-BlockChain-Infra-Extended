use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod contract {
    use super::*;

    pub fn solve(ctx: Context<Solve>) -> Result<()> {
        let storage = &mut ctx.accounts.storage;
        storage.solved = true;
        Ok(())
    }

    pub fn is_solved(ctx: Context<IsSolved>) -> Result<bool> {
        let storage = &ctx.accounts.storage;
        Ok(storage.solved)
    }
}

#[derive(Accounts)]
pub struct Solve<'info> {
    #[account(mut)]
    pub storage: Account<'info, Storage>,
}

#[derive(Accounts)]
pub struct IsSolved<'info> {
    pub storage: Account<'info, Storage>,
}

#[account]
pub struct Storage {
    pub solved: bool,
}
