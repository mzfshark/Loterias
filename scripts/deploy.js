const { ethers, network } = require("hardhat");

async function main() {
    // Fetch environment variables
    const deployerPrivateKey = process.env.DEPLOYER_PRIVATE_KEY;
    const vrfCoordinatorAddress = process.env.VRF_COORDINATOR_ADDRESS;
    const keyHash = process.env.KEY_HASH;
    const subscriptionId = process.env.SUBSCRIPTION_ID;
    const projectFunds = process.env.PROJECT_FUNDS;
    const grantFund = process.env.GRANT_FUND;
    const operationFund = process.env.OPERATION_FUND;

    if (!deployerPrivateKey || !vrfCoordinatorAddress || !keyHash || !subscriptionId || !projectFunds || !grantFund || !operationFund) {
        console.error("Missing required environment variables.");
        process.exit(1);
    }

    // Set up deployer
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);

    // Contract factory
    const LottOneFactory = await ethers.getContractFactory("LottOne");

    // Deployment parameters
    const oneTokenAddress = "YOUR_ERC20_TOKEN_ADDRESS"; // Replace with actual token address
    const networkId = network.config.chainId;
    console.log(`Deploying to network ID: ${networkId}`);

    // Deploy the contract
    const lottOne = await LottOneFactory.deploy(
        oneTokenAddress,
        vrfCoordinatorAddress,
        keyHash,
        subscriptionId,
        projectFunds,
        grantFund,
        operationFund
    );

    console.log("Deploying contract...");
    await lottOne.deployed();

    console.log("LottOne deployed to:", lottOne.address);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
