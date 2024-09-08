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
      url: RPC_URL_MAINNET,
    },
    sepolia: {
      url: RPC_URL_SEPOLIA,
    },
    harmony: {
      url: RPC_URL_HARMONY,
    },
    bsc: {
      url: RPC_URL_BSC,
    },
    bsc_testnet: {
      url: RPC_URL_BSC_TESTNET,
    },
    opBNB: {
      url: RPC_URL_OPBNB,
    },
    opBNB_testnet: {
      url: RPC_URL_OPBNB_TESTNET,
    }
  },
  /*etherscan: {
    apiKey: {
      // Your etherscan API key if needed for verification
    }
  }*/
};
