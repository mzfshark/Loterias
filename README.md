Here's a comprehensive `README.md` for the `LottOne` Solidity contract, suitable for a GitHub repository:

# LottOne - A Decentralized Lottery Contract

## Overview

`LottOne` is a Solidity smart contract that implements a decentralized lottery system on the Ethereum blockchain. It utilizes Chainlink's Verifiable Random Function (VRF) to securely generate random numbers and ERC20 tokens for ticket purchases and prize payouts.

## Features

- **Decentralized Lottery**: Operates on the Ethereum blockchain with transparency and security.
- **Chainlink VRF Integration**: Uses Chainlink VRF for secure and verifiable random number generation.
- **ERC20 Token Integration**: Supports ticket purchases and prize payouts in ERC20 tokens.
- **Dynamic Ticket Pricing**: Allows adjustment of ticket prices by the contract owner.
- **Agent Commission**: Agents receive a commission for selling tickets, with higher commissions for electronic sales.
- **Prize Distribution**: Automatically calculates and distributes prizes based on ticket matches.

## Contract Details

### Contract: `LottOne`

#### State Variables

- `IERC20 public oneToken`: ERC20 token used for transactions.
- `address public owner`: Address of the contract owner.
- `uint256 public ticketPrice`: Price of a ticket in ONE tokens.
- `uint8 public totalNumbers`: Total number of possible lottery numbers.
- `uint8 public minNumbers`: Minimum numbers a ticket can choose.
- `uint8 public maxNumbers`: Maximum numbers a ticket can choose.
- `uint256 public drawInterval`: Time interval between lottery draws.
- `uint256 public lastDrawTime`: Timestamp of the last draw.
- `uint256 public prizePool`: Total prize pool accumulated from ticket sales.

#### Chainlink VRF Variables

- `VRFCoordinatorV2Interface COORDINATOR`: Interface for Chainlink VRF Coordinator.
- `uint64 public subscriptionId`: Chainlink VRF subscription ID.
- `bytes32 public keyHash`: Key hash for Chainlink VRF.
- `uint16 requestConfirmations`: Number of confirmations required from Chainlink VRF.
- `uint32 callbackGasLimit`: Gas limit for VRF callback.
- `uint32 numWords`: Number of random words requested from Chainlink VRF.
- `uint256[] public randomWords`: Array of random words received from Chainlink VRF.
- `uint256 public requestId`: ID of the VRF request.

#### Structures

- `struct Ticket`: Represents a lottery ticket with player details, chosen numbers, and sales information.

#### Mappings

- `mapping(address => uint256) public winnings`: Tracks player winnings.
- `mapping(address => uint256) public agentCommissions`: Tracks commissions for agents.

#### Events

- `event TicketPurchased(address indexed player, uint8[] chosenNumbers, address agent, bool isElectronic)`: Emitted when a ticket is purchased.
- `event DrawResult(uint8[] winningNumbers)`: Emitted when draw results are available.
- `event PrizeClaimed(address indexed player, uint256 amount)`: Emitted when a player claims their prize.
- `event AgentCommissionPaid(address indexed agent, uint256 amount)`: Emitted when an agent claims their commission.
- `event RandomWordsRequested(uint256 requestId)`: Emitted when random words are requested from Chainlink VRF.

### Functions

- `purchaseTicket(uint8[] memory _chosenNumbers, bool _isElectronic, address _agent) external`: Allows users to purchase a lottery ticket.
- `draw() external onlyOwner`: Initiates a lottery draw.
- `fulfillRandomWords(uint256, uint256[] memory _randomWords) internal override`: Callback function from Chainlink VRF for processing random words.
- `distributePrizes() internal`: Distributes the prize pool among winners and manages other allocations.
- `getMatchCount(uint8[] memory _chosenNumbers) internal view returns (uint8)`: Calculates the number of matches between chosen numbers and winning numbers.
- `claimPrize() external`: Allows players to claim their winnings.
- `claimAgentCommission() external`: Allows agents to claim their commissions.
- `updateTicketPrice(uint256 _newPrice) external onlyOwner`: Allows the owner to update the ticket price.
- `withdrawFunds(uint256 _amount) external onlyOwner`: Allows the owner to withdraw funds from the contract.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/lottone.git
   cd lottone
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Compile the contract:
   ```bash
   npx hardhat compile
   ```

4. Deploy the contract:
   ```bash
   npx hardhat run scripts/deploy.js --network yourNetwork
   ```

## Usage

1. **Purchase Ticket**: Call `purchaseTicket` with chosen numbers, whether the ticket is electronic, and the agent's address.
2. **Draw**: Call `draw` to initiate a lottery draw.
3. **Claim Prize**: Call `claimPrize` to claim any winnings.
4. **Claim Agent Commission**: Call `claimAgentCommission` to claim commissions as an agent.
5. **Update Ticket Price**: Call `updateTicketPrice` to set a new ticket price.
6. **Withdraw Funds**: Call `withdrawFunds` to withdraw funds as the owner.

## Security Considerations

- Ensure proper testing and auditing of the contract before deployment.
- Chainlink VRF provides secure random number generation, but always review integration for potential vulnerabilities.

## License

MIT License. See `LICENSE` file for details.

## Contact

For any questions or issues, please open an issue on GitHub or contact [contact@axodus.finance](mailto:contact@axodus.finance).



Feel free to adjust the links, email address, and installation steps according to your specific setup and repository details.
