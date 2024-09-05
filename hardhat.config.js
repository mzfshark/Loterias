require('@nomiclabs/hardhat-ethers');
require('dotenv').config();


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
      //accounts: $INFURA_PROJECT_SECRET
    },
    /*bsc: {
      url: `https://bsc-mainnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      accounts: ${{ secrets.INFURA_PROJECT_SECRET }}
    },
    bsc_testnet: {
      url: `https://bsc-testnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      accounts: ${{ secrets.INFURA_PROJECT_SECRET }}
    },
    opBNB: {
      url: `https://opbnb-mainnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      accounts: ${{ secrets.INFURA_PROJECT_SECRET }}
    },
    opBNB_testnet: {
      url: `https://opbnb-testnet.infura.io/v3/554262fab79f49adb4fdba2db2587800`,
      accounts: ${{ secrets.INFURA_PROJECT_SECRET }}
    },*/
  },
};
