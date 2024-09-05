require('@nomiclabs/hardhat-ethers');
require('dotenv').config();

// Get environment variables
const { INFURA_PROJECT_ID, INFURA_PROJECT_SECRET, DEPLOYER_PRIVATE_KEY } = process.env;

// Validate environment variables
if (!DEPLOYER_PRIVATE_KEY || DEPLOYER_PRIVATE_KEY.length !== 64) {
  throw new Error("Invalid DEPLOYER_PRIVATE_KEY: Ensure it is set and 64 characters long.");
}
if (!INFURA_PROJECT_ID) {
  throw new Error("INFURA_PROJECT_ID is not set in environment variables.");
}
if (!INFURA_PROJECT_SECRET) {
  throw new Error("INFURA_PROJECT_SECRET is not set in environment variables.");
}

module.exports = {
  solidity: "0.8.7",
  networks: {
    hardhat: {},
    // Add other networks here if needed
    // e.g., ropsten: {
    //   url: `https://ropsten.infura.io/v3/YOUR_INFURA_PROJECT_ID`,
    //   accounts: [`0x${YOUR_PRIVATE_KEY}`]
    // }
    harmony: {
      url: `https://api.harmony.one`,
      chainId: 1666600000,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`] 
    },
    bsc: {
      url: `https://bsc-mainnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    bsc_testnet: {
      url: `https://bsc-testnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    opBNB: {
      url: `https://opbnb-mainnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    opBNB_testnet: {
      url: `https://opbnb-testnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
  },
};
