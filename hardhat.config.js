require('@nomiclabs/hardhat-ethers');

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
      url: `https://api.harmony.one`
    },
    bsc: {
      url: `https://bsc-mainnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`
    },
    bsc_testnet: {
      url: `https://bsc-testnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`
    },
    opBNB: {
      url: `https://opbnb-mainnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`
    },
    opBNB_testnet: {
      url: `https://opbnb-testnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`
    },
  },
};
