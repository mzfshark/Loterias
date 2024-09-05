const hre = require("hardhat");

async function main() {
  // Get the contract factory
  const LottOne = await hre.ethers.getContractFactory("LottOne");

  // Define constructor arguments
  const oneTokenAddress = "0xf59de020d650e69ef0755bf37f3d16b80ee132f5"; // Replace with the actual ONE token address
  const vrfCoordinatorAddress = "0x..."; // Replace with the actual VRF Coordinator address
  const keyHash = "0x..."; // Replace with the actual keyHash
  const subscriptionId = 1; // Replace with the actual subscription ID

  // Deploy the contract
  const lottOne = await LottOne.deploy(oneTokenAddress, vrfCoordinatorAddress, keyHash, subscriptionId);

  await lottOne.deployed();

  console.log("LottOne deployed to:", lottOne.address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
