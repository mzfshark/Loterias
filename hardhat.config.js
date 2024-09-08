require('@nomiclabs/hardhat-ethers');
require('@nomiclabs/hardhat-etherscan');
require('dotenv').config();

// Load environment variables
const { 
  RPC_URL_MAINNET, RPC_URL_SEPOLIA, RPC_URL_HARMONY, RPC_URL_BSC, RPC_URL_BSC_TESTNET, RPC_URL_OPBNB, RPC_URL_OPBNB_TESTNET, 
  DEPLOYER_PRIVATE_KEY 
} = process.env;

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
      chainId: 1,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    sepolia: {
      url: RPC_URL_SEPOLIA,
      chainId: 11155111,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    harmony: {
      url: RPC_URL_HARMONY,
      chainId: 1666600000,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    bsc: {
      url: RPC_URL_BSC,
      chainId: 56,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    bsc_testnet: {
      url: RPC_URL_BSC_TESTNET,
      chainId: 97,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    opBNB: {
      url: RPC_URL_OPBNB,
      chainId: 100,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    opBNB_testnet: {
      url: RPC_URL_OPBNB_TESTNET,
      chainId: 101,
      accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    }
  },
  // Uncomment and configure this section if you need Etherscan verification
  /* etherscan: {
    apiKey: {
      // Your etherscan API key if needed for verification
    }
  } */
};
