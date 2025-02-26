const anchor = require('@coral-xyz/anchor');
const bs58 = require('bs58');
const { SystemProgram, Keypair, PublicKey } = anchor.web3;

// Replace these values with your own
PLAYER_KEYPAIR = "3LW2JrTSHA5CtbrXDRKHs1Nrjk5Z6BaiGeWmLtok5AHGJ6ndEf8R9qfKJ76pdYJgca5UNWH8GnRcc7mTi4cKk5Mf"
CTX_PUBKEY = "2xDs68ZkNTFSJymfiGa7H43mGJxwe7qJR5oNkqgmosBG"
PROGRAM_ID = "GwzDES36sT6CNqWmbMe9QpfxrAinWPwHvBNBNSfA3ejg"
RPC_URL = "http://localhost:48334/bd02b6dd-66bf-48fb-bf23-d7595f525c79"

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
