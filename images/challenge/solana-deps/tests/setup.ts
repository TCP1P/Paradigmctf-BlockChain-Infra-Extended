import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { Setup } from "../target/types/setup";
import { Connection, PublicKey, LAMPORTS_PER_SOL } from "@solana/web3.js";

const jsonRPCUrl = process.env.jsonRPCUrl;
const solvedAccount = process.env.solvedAccount;
const systemProgram = process.env.systemProgram;
const systemUser = process.env.systemUser;

describe("setup", () => {
  const connection = new Connection(jsonRPCUrl, "finalized");
  // Configure the provider with the connection.
  anchor.setProvider({ connection });

  const program = anchor.workspace.Setup as Program<Setup>;

  it("initialize program", async () => {
    const tx = await program.methods.initialize().accounts({
      solvedAccount,
      systemProgram,
      user: systemUser
    }).rpc();
    console.log("Your transaction signature", tx);
  });
});
