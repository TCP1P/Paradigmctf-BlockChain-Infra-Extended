const anchor = require('@coral-xyz/anchor');
const bs58 = require('bs58');
const { SystemProgram, Keypair, PublicKey } = anchor.web3;

// Replace these values with your own
PLAYER_KEYPAIR = "27t5ChLAq22uJJhnVrgAHcd4PbYQVL5EroYETCDynoHF3oKvfPpWcw5gDYq91HBgJD4yp6rFy4BjewMMJufaeKUu"
CTX_PUBKEY = "H2qgAjUu8GxpmL15dozGxsPgpbMFe1p7f6SSvCsmXXnx"
PROGRAM_ID = "GwzDES36sT6CNqWmbMe9QpfxrAinWPwHvBNBNSfA3ejg"
RPC_URL = "http://0.0.0.0:48334/7a795e4f-61e2-4b51-8be2-d38a84d4e0be"

const main = async () => {
  // Create a connection to the cluster
  const connection = new anchor.web3.Connection(RPC_URL, 'confirmed');

  // Decode the base58 secret key to create the wallet keypair
  const secretKey = bs58.default.decode(PLAYER_KEYPAIR);
  const walletKeypair = Keypair.fromSecretKey(secretKey);
  const wallet = new anchor.Wallet(walletKeypair);

  // Create a provider and set it as the default
  const provider = new anchor.AnchorProvider(connection, wallet, { preflightCommitment: 'confirmed' });
  anchor.setProvider(provider);

  // Fetch your program's IDL from the JSON RPC
  const programId = new PublicKey(PROGRAM_ID);
  const program = await anchor.Program.at(programId, provider);

  // Define the context account public key
  const ctxPubkey = new PublicKey(CTX_PUBKEY);

  // Call the "solve" instruction
  const txSolve = await program.transaction.solve({
    accounts: {
      solvedAccount: ctxPubkey,
      user: provider.wallet.publicKey,
      systemProgram: SystemProgram.programId,
    },
  });
  console.log("Solve tx:", txSolve);

  // Call the "is_solved" instruction
  // Note: If your IDL uses snake_case for instruction names, AnchorJS will convert it to camelCase.
  const txIsSolved = await program.views.isSolved({
    accounts: {
      solvedAccount: ctxPubkey,
      user: provider.wallet.publicKey,
      systemProgram: SystemProgram.programId,
    },
  });
  console.log("Is solved?", txIsSolved);
};
main()
