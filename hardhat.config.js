require('@nomiclabs/hardhat-ethers');
require('@nomiclabs/hardhat-etherscan');
require('dotenv').config();

// Load environment variables
const { RPC_URL_BSC, RPC_URL_BSC_TESTNET, RPC_URL_HARMONY, RPC_URL_OPBNB, RPC_URL_OPBNB_TESTNET, RPC_URL_SEPOLIA, DEPLOYER_PRIVATE_KEY } = process.env;

module.exports = {
  solidity: {
    version: "0.8.7",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    mainnet: {
    },
    sepolia: {
    },
    harmony: {
    },
    bsc: {
    },
    bsc_testnet: {
    },
    opBNB: {
    },
    opBNB_testnet: {
    }
  },
  /*etherscan: {
    apiKey: {
      // Your etherscan API key if needed for verification
    }
  }*/
};
