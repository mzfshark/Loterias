# LottOne Contract Documentation

## Overview

`LottOne` is a Solidity smart contract that implements a lottery system using ERC20 tokens and Chainlink VRF (Verifiable Random Function) for randomness. The contract allows users to purchase lottery tickets, participates in lottery draws, and manages prize distribution. The contract is built on Solidity version 0.8.7 and uses the OpenZeppelin and Chainlink libraries.

## Prerequisites

- **ERC20 Token**: The contract relies on an ERC20 token (`oneToken`) for ticket purchases and prize distribution.
- **Chainlink VRF**: Used to provide verifiable randomness for drawing winning numbers.

## Imports

- `IERC20` from OpenZeppelin: Interface for ERC20 token operations.
- `VRFConsumerBaseV2` from Chainlink: Base contract for Chainlink VRF integration.
- `VRFCoordinatorV2Interface` from Chainlink: Interface for interacting with the VRF Coordinator.

## State Variables

- `IERC20 public oneToken`: Instance of the ERC20 token used for transactions.
- `address public owner`: Address of the contract owner.
- `uint256 public ticketPrice`: Price of a ticket in `oneToken` (default: 1 ONE token).
- `uint8 public totalNumbers`: Total number of possible numbers in the lottery (default: 25).
- `uint8 public minNumbers`: Minimum number of numbers a ticket must have (default: 15).
- `uint8 public maxNumbers`: Maximum number of numbers a ticket can have (default: 20).
- `uint256 public drawInterval`: Time interval between draws (default: 7 days).
- `uint256 public lastDrawTime`: Timestamp of the last draw.
- `uint256 public prizePool`: Total amount collected for the prize pool.

### Chainlink VRF Variables

- `VRFCoordinatorV2Interface COORDINATOR`: Instance of the Chainlink VRF Coordinator.
- `uint64 public subscriptionId`: Chainlink VRF subscription ID.
- `bytes32 public keyHash`: Key hash for Chainlink VRF.
- `uint16 requestConfirmations`: Number of confirmations for VRF requests (default: 3).
- `uint32 callbackGasLimit`: Gas limit for the callback function (default: 100,000).
- `uint32 numWords`: Number of random words needed (default: 15).
- `uint256[] public randomWords`: Array to store random words received from VRF.
- `uint256 public requestId`: Request ID for VRF.

## Structs

- `Ticket`: Represents a lottery ticket.
  - `address player`: Address of the ticket purchaser.
  - `uint8[] chosenNumbers`: Array of numbers chosen by the player.
  - `bool isElectronic`: Indicates if the ticket was purchased electronically.
  - `address agent`: Address of the agent who sold the ticket.

## Mappings

- `mapping(address => uint256) public winnings`: Tracks winnings for each player.
- `mapping(address => uint256) public agentCommissions`: Tracks commissions for each agent.

## Events

- `event TicketPurchased(address indexed player, uint8[] chosenNumbers, address agent, bool isElectronic)`: Emitted when a ticket is purchased.
- `event DrawResult(uint8[] winningNumbers)`: Emitted when the draw results are available.
- `event PrizeClaimed(address indexed player, uint256 amount)`: Emitted when a player claims a prize.
- `event AgentCommissionPaid(address indexed agent, uint256 amount)`: Emitted when an agent's commission is paid.
- `event RandomWordsRequested(uint256 requestId)`: Emitted when random words are requested from Chainlink VRF.

## Functions

### Constructor

```solidity
constructor(address _oneToken, address _vrfCoordinator, bytes32 _keyHash, uint64 _subscriptionId)

