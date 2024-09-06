# CryptoDraw

CryptoDraw is a decentralized, blockchain-based lottery system built on Ethereum and compatible networks. Utilizing Chainlink VRF (Verifiable Random Function) for secure and transparent random number generation, CryptoDraw offers a fair and verifiable lottery experience. The platform allows users to purchase tickets with their chosen numbers and participate in regular draws to win various prizes, including jackpots.

## Key Features

- **Decentralized Lottery System**: Fully decentralized and powered by smart contracts, ensuring transparency and fairness.
- **Chainlink VRF Integration**: Uses Chainlink's Verifiable Random Function (VRF) to ensure that the winning numbers are provably random.
- **Agent Commission System**: Allows agents to sell tickets and earn commissions based on sales volume.
- **Secure and Efficient**: Built using Solidity and audited libraries such as OpenZeppelin for robust security.
- **Multi-Network Support**: Deployable on multiple networks like Ethereum Mainnet, Sepolia, Harmony, BSC, and more.

## Smart Contract Overview

- **LottoChain**: The main contract that manages ticket purchases, draws, random number generation, and prize distribution.
- **IERC20**: Interface for ERC20 token interactions, used for ticket purchases and prize payouts.
- **VRFConsumerBaseV2**: Chainlink's contract for VRF integration, ensuring secure and random number generation.
- **Ownable**: Provides ownership control over the contract functions, allowing only the contract owner to modify key parameters.

## Installation

To get started with CryptoDraw, clone the repository and install the dependencies:

```bash
git clone https://github.com/your-repo/CryptoDraw.git
cd CryptoDraw
npm install
```

## Deployment

1. **Configure Environment Variables**: Set up your environment variables in a `.env` file. Ensure you have the following variables configured:

    ```plaintext
    DEPLOYER_PRIVATE_KEY=<your_private_key>
    RPC_URL_<NETWORK_NAME>=<your_rpc_url>
    VRF_COORDINATOR_ADDRESS=<chainlink_vrf_coordinator_address>
    KEY_HASH=<your_key_hash>
    SUBSCRIPTION_ID=<your_subscription_id>
    NATIVE_TOKEN_<NETWORK_NAME>=<token_address>
    PROJECT_FUNDS=<project_fund_allocation>
    GRANT_FUND=<grant_fund_allocation>
    OPERATION_FUND=<operation_fund_allocation>
    ```

2. **Deploy Smart Contracts**: Deploy the contracts using Hardhat by running:

    ```bash
    npx hardhat run scripts/deploy.js --network <network_name>
    ```

## Usage

- **Purchase a Ticket**: Users can purchase a ticket by choosing their numbers and paying the ticket price in the designated token.
- **Draw Execution**: The contract automatically checks if a draw is due using Chainlink Keepers and executes the draw using Chainlink VRF for random number generation.
- **Prize Distribution**: Winners are automatically rewarded based on the number of matches with the drawn numbers. Agents receive their commissions for ticket sales.

## Security

CryptoDraw uses audited libraries and implements several safety checks to ensure the integrity of the lottery system:

- Chainlink VRF for secure and unbiased random number generation.
- Use of OpenZeppelin's contracts for safe and standardized smart contract functions.
- Regular updates and checks to maintain security best practices.

## Testing

Run the tests to ensure that everything is working as expected:

```bash
npx hardhat test
```

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your improvements. Make sure to adhere to the project's coding standards and include relevant tests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or support, please reach out to [your_email@example.com](mailto:your_email@example.com).

---

Enjoy participating in a fair, transparent, and decentralized lottery with CryptoDraw!

This `README.md` provides a comprehensive introduction to the CryptoDraw project, outlines its core functionality, and guides users on how to install, deploy, and use the project. It also includes sections on security, testing, contributing, and licensing.



Feel free to adjust the links, email address, and installation steps according to your specific setup and repository details.
