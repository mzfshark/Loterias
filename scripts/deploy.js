const { ethers, network } = require("hardhat");

async function main() {
    // Fetch environment variables
    const deployerPrivateKey = process.env.DEPLOYER_PRIVATE_KEY;
    const vrfCoordinatorAddress = process.env.VRF_COORDINATOR_ADDRESS;
    const keyHash = process.env.KEY_HASH;
    const subscriptionId = process.env.SUBSCRIPTION_ID;
    const initialProjectFund = process.env.INITIAL_PROJECT_FUND;
    const initialGrantFund = process.env.INITIAL_GRANT_FUND;
    const initialOperationFund = process.env.INITIAL_OPERATION_FUND;
    const nativeTokenAddress = process.env.NATIVE_TOKEN_ADDRESS;

    // Validate environment variables
    if (!deployerPrivateKey || !vrfCoordinatorAddress || !keyHash || !subscriptionId || 
        !initialProjectFund || !initialGrantFund || !initialOperationFund || !nativeTokenAddress) {
        console.error("Missing required environment variables.");
        process.exit(1);
    }

    // Set up deployer
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);
    console.log(`Account balance: ${(await deployer.getBalance()).toString()}`);

    // Contract factory
    const LottoChainFactory = await ethers.getContractFactory("LottoChain");

    // Deployment parameters
    const networkId = network.config.chainId;
    console.log(`Deploying to network ID: ${networkId}`);

    // Deploy the contract
    const lottoChain = await LottoChainFactory.deploy(
        nativeTokenAddress,
        vrfCoordinatorAddress,
        keyHash,
        subscriptionId,
        ethers.utils.parseUnits(initialProjectFund, "ether"),
        ethers.utils.parseUnits(initialGrantFund, "ether"),
        ethers.utils.parseUnits(initialOperationFund, "ether")
    );

    console.log("Deploying contract...");
    await lottoChain.deployed();

    console.log("LottoChain deployed to:", lottoChain.address);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
