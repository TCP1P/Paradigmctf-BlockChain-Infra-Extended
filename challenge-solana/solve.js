const anchor = require('@coral-xyz/anchor');
const bs58 = require('bs58');
const { SystemProgram, Keypair, PublicKey } = anchor.web3;

// Replace these values with your own
PLAYER_KEYPAIR = "3gzKuuWaCj531ixVYHYaZmoAZ2JgQRdwuqc1WSv2YwWnDVAXkMWmMtmcRtSGagX8EXhfmRyZPmV7QJuAjB3MoLPG"
CTX_PUBKEY = "3FanPCGb2Uo8vAzW4npTfhXkJcoUVVatdCStwkPppzN4"
PROGRAM_ID = "3uJ1MWUmG9AuQgU5ymQLFLEF7xagk2WPHCAYdWDHBAZN"
RPC_URL = "http://localhost:48334/9925c004-2f89-4295-a23b-3b006c0364ba"

const main = async () => {
  // Create a connection to the cluster
  const connection = new anchor.web3.Connection(RPC_URL);

  // Decode the base58 secret key to create the wallet keypair
  const secretKey = bs58.default.decode(PLAYER_KEYPAIR);
  const walletKeypair = Keypair.fromSecretKey(secretKey);
  const wallet = new anchor.Wallet(walletKeypair);

  // Create a provider and set it as the default
  const provider = new anchor.AnchorProvider(connection, wallet, { commitment: "finalized" });
  anchor.setProvider(provider);

  // Fetch your program's IDL from the JSON RPC
  const programId = new PublicKey(PROGRAM_ID);
  const program = await anchor.Program.at(programId, provider);

  // Define the context account public key
  const ctxPubkey = new PublicKey(CTX_PUBKEY);

  // Call the "solve" instruction
  const txSolve = await program.methods.solve().accounts({
      solvedAccount: ctxPubkey,
      user: provider.wallet.publicKey,
      systemProgram: SystemProgram.programId,
  }).transaction();
  const txSolveSignature = await connection.sendTransaction(txSolve, [wallet.payer])
  console.log("Solve tx:", txSolveSignature);

  let isSolved = false;
  while (!isSolved) {
    const txIsSolved = await program.views.isSolved({
      accounts: {
        solvedAccount: ctxPubkey,
        user: provider.wallet.publicKey,
        systemProgram: SystemProgram.programId,
      },
    });
    if (txIsSolved) {
      isSolved = true;
      console.log("Challenge solved successfully.");
    } else {
      console.log("Challenge not yet solved. Trying again...");
      await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second before trying again
    }
  }
};
main()
