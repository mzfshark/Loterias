### LottOne Contract Documentation

Here's the documentation for the Solidity contract `LottOne`. This contract implements a lottery system integrated with Chainlink VRF (Verifiable Random Function) for secure random number generation and uses ERC20 tokens for transactions.

#### SPDX-License-Identifier
```solidity
// SPDX-License-Identifier: MIT
```
- Specifies the license under which the contract code is distributed.

#### Pragma
```solidity
pragma solidity ^0.8.7;
```
- Indicates the Solidity compiler version required for this contract.

#### Imports
```solidity
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
```
- Imports the ERC20 token interface from OpenZeppelin and Chainlink VRF consumer base and coordinator interface.

#### Contract: `LottOne`
Inherits from `VRFConsumerBaseV2` to use Chainlink's VRF for random number generation.

**State Variables:**

- `IERC20 public oneToken`: ERC20 token used for ticket purchases and prize payouts.
- `address public owner`: Address of the contract owner.
- `uint256 public ticketPrice`: Price of a ticket in ONE tokens.
- `uint8 public totalNumbers`: Total number of possible numbers in the lottery.
- `uint8 public minNumbers`: Minimum number of numbers a ticket must choose.
- `uint8 public maxNumbers`: Maximum number of numbers a ticket can choose.
- `uint256 public drawInterval`: Time interval between draws.
- `uint256 public lastDrawTime`: Timestamp of the last draw.
- `uint256 public prizePool`: Total prize pool accumulated from ticket sales.

**Chainlink VRF Variables:**

- `VRFCoordinatorV2Interface COORDINATOR`: Interface for Chainlink VRF Coordinator.
- `uint64 public subscriptionId`: Chainlink VRF subscription ID.
- `bytes32 public keyHash`: Key hash for Chainlink VRF.
- `uint16 requestConfirmations`: Number of confirmations required from Chainlink VRF.
- `uint32 callbackGasLimit`: Gas limit for VRF callback.
- `uint32 numWords`: Number of random words requested from Chainlink VRF.
- `uint256[] public randomWords`: Array of random words received from Chainlink VRF.
- `uint256 public requestId`: ID of the VRF request.

**Structures:**

- `struct Ticket`: Represents a lottery ticket with details including the player, chosen numbers, whether the ticket was sold electronically, and the agent who sold it.

**Mappings:**

- `mapping(address => uint256) public winnings`: Tracks the winnings of each player.
- `mapping(address => uint256) public agentCommissions`: Tracks the commissions for agents.

**Events:**

- `event TicketPurchased(address indexed player, uint8[] chosenNumbers, address agent, bool isElectronic)`: Emitted when a ticket is purchased.
- `event DrawResult(uint8[] winningNumbers)`: Emitted when the draw results are available.
- `event PrizeClaimed(address indexed player, uint256 amount)`: Emitted when a player claims their prize.
- `event AgentCommissionPaid(address indexed agent, uint256 amount)`: Emitted when an agent claims their commission.
- `event RandomWordsRequested(uint256 requestId)`: Emitted when random words are requested from Chainlink VRF.

**Constructor:**
```solidity
constructor(address _oneToken, address _vrfCoordinator, bytes32 _keyHash, uint64 _subscriptionId)
    VRFConsumerBaseV2(_vrfCoordinator)
```
- Initializes the contract with the address of the ERC20 token, VRF coordinator, key hash, and subscription ID.

**Modifiers:**

- `onlyOwner`: Restricts function access to the contract owner.

**Functions:**

- `function purchaseTicket(uint8[] memory _chosenNumbers, bool _isElectronic, address _agent) external`: Allows users to purchase a lottery ticket.
- `function draw() external onlyOwner`: Initiates a lottery draw.
- `function fulfillRandomWords(uint256, uint256[] memory _randomWords) internal override`: Callback function from Chainlink VRF that processes the random words.
- `function distributePrizes() internal`: Distributes the prize pool among winners and manages other allocations.
- `function getMatchCount(uint8[] memory _chosenNumbers) internal view returns (uint8)`: Calculates how many of the chosen numbers match the winning numbers.
- `function claimPrize() external`: Allows players to claim their winnings.
- `function claimAgentCommission() external`: Allows agents to claim their commissions.
- `function updateTicketPrice(uint256 _newPrice) external onlyOwner`: Allows the owner to update the ticket price.
- `function withdrawFunds(uint256 _amount) external onlyOwner`: Allows the owner to withdraw funds from the contract.

This documentation should give you a clear understanding of the contract's functionality and how each part works together to implement the lottery system.
