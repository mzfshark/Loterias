require('@nomiclabs/hardhat-ethers');
require('@nomiclabs/hardhat-etherscan');
require('dotenv').config();

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
      url: [],
      chainId: 1,
    },
    sepolia: {
      url: [],
      chainId: 11155111,
    },
    harmony: {
      url: [],
      chainId: 1666600000,
    },
    bsc: {
      url: [],
      chainId: 56,
    },
    bsc_testnet: {
      url: [],
      chainId: 97,
    },
    opBNB: {
      url: [],
      chainId: 100,
    },
    opBNB_testnet: {
      url: [],
      chainId: 101,
    }
  },
  // Uncomment and configure this section if you need Etherscan verification
  /* etherscan: {
    apiKey: {
      // Your etherscan API key if needed for verification
    }
  } */
};
