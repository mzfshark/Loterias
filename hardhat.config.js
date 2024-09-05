require('@nomiclabs/hardhat-ethers');
require('dotenv').config();

const { DEPLOYER_PRIVATE_KEY } = process.env;

if (!DEPLOYER_PRIVATE_KEY || DEPLOYER_PRIVATE_KEY.length !== 64) {
  throw new Error("Invalid DEPLOYER_PRIVATE_KEY: Ensure it is set and 64 characters long.");
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
      chainId: 1666600000
      //accounts: [`0x${DEPLOYER_PRIVATE_KEY}`] 
    },
    bsc: {
      url: `https://bsc-mainnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      //accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    bsc_testnet: {
      url: `https://bsc-testnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      //accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    opBNB: {
      url: `https://opbnb-mainnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      //accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
    opBNB_testnet: {
      url: `https://opbnb-testnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      //accounts: [`0x${DEPLOYER_PRIVATE_KEY}`]
    },
  },
};
