## CryptoDraw Contract Documentation

### Overview

The `CryptoDraw` contract is a lottery system implemented in Solidity. It integrates Chainlink services for randomness and automated upkeep, and leverages OpenZeppelin contracts for security and access control. Players purchase tickets to participate in the lottery, and winning numbers are drawn using Chainlink VRF. The contract handles ticket purchases, prize distribution, and agent commissions.

### Dependencies

- **OpenZeppelin Contracts:**
  - `IERC20`: Interface for ERC20 token standard.
  - `Ownable`: Provides basic authorization control functions, simplifying the implementation of user permissions.
  - `AccessControl`: Provides role-based access control mechanism.
  - `ReentrancyGuard`: Prevents reentrant calls to functions.

- **Chainlink Contracts:**
  - `VRFConsumerBaseV2`: Base contract for consuming Chainlink VRF (Verifiable Random Function).
  - `VRFCoordinatorV2Interface`: Interface for interacting with the VRF Coordinator.
  - `AggregatorV3Interface`: Interface for Chainlink Price Feeds.
  - `KeeperCompatibleInterface`: Interface for Chainlink Keepers (automation).

### Contract Details

#### State Variables

- **`nativeTokenAddress`**: Address of the ERC20 token used for transactions.
- **`priceFeed`**: Chainlink Price Feed used to fetch the USD to native token conversion rate.
- **`ticketPriceUSD`**: Price of a ticket in USD (1 USD by default).
- **`totalNumbers`**: Total number of possible numbers in the lottery (25).
- **`minNumbers`**: Minimum number of numbers a player must choose (15).
- **`maxNumbers`**: Maximum number of numbers a player can choose (20).
- **`drawInterval`**: Interval between lottery draws (4 days by default).
- **`lastDrawTime`**: Timestamp of the last draw.
- **`prizePool`**: Total pool of funds accumulated from ticket purchases.

- **Chainlink VRF Variables:**
  - **`COORDINATOR`**: Address of the Chainlink VRF Coordinator.
  - **`subscriptionId`**: Subscription ID for Chainlink VRF.
  - **`keyHash`**: Key hash for Chainlink VRF.
  - **`requestConfirmations`**: Number of confirmations required by Chainlink VRF.
  - **`callbackGasLimit`**: Gas limit for the callback function from Chainlink VRF.
  - **`numWords`**: Number of random words needed for generating winning numbers (15).

- **Funds:**
  - **`projectFund`**: Fund allocated for the project's use.
  - **`grantFund`**: Fund allocated for grants.
  - **`operationFund`**: Fund allocated for operational expenses.

- **`tickets`**: Array of `Ticket` structs, each representing a purchased ticket.
- **`winningNumbers`**: Array of winning numbers drawn in the latest lottery.
- **`winnings`**: Mapping from player addresses to their accumulated winnings.
- **`agentCommissions`**: Mapping from agent addresses to their accumulated commissions.

#### Structs

- **`Ticket`**:
  - **`player`**: Address of the player who purchased the ticket.
  - **`chosenNumbers`**: Array of numbers chosen by the player.
  - **`agent`**: Address of the agent who sold the ticket.

#### Events

- **`TicketPurchased(address indexed player, uint8[] chosenNumbers, address agent)`**: Emitted when a ticket is purchased.
- **`DrawResult(uint8[] winningNumbers)`**: Emitted when winning numbers are drawn.
- **`PrizeClaimed(address indexed player, uint256 amount)`**: Emitted when a player claims their prize.
- **`AgentCommissionPaid(address indexed agent, uint256 amount)`**: Emitted when an agent receives a commission payment.
- **`RandomWordsRequested(uint256 requestId)`**: Emitted when a request for random words is made to Chainlink VRF.

#### Modifiers

- **`onlyRole(bytes32 role)`**: Restricts access to functions based on the specified role.

#### Constructor

```solidity
constructor(
    address _nativeTokenAddress,
    address _vrfCoordinator,
    bytes32 _keyHash,
    uint64 _subscriptionId,
    address _priceFeedAddress,
    uint256 _initialProjectFund,
    uint256 _initialGrantFund,
    uint256 _initialOperationFund
)
    VRFConsumerBaseV2(_vrfCoordinator)
```

- **Parameters:**
  - **`_nativeTokenAddress`**: Address of the ERC20 token.
  - **`_vrfCoordinator`**: Address of the Chainlink VRF Coordinator.
  - **`_keyHash`**: Key hash for Chainlink VRF.
  - **`_subscriptionId`**: Subscription ID for Chainlink VRF.
  - **`_priceFeedAddress`**: Address of the Chainlink Price Feed.
  - **`_initialProjectFund`**: Initial allocation for the project fund.
  - **`_initialGrantFund`**: Initial allocation for the grant fund.
  - **`_initialOperationFund`**: Initial allocation for the operation fund.

#### Functions

- **`purchaseTicket(uint8[] calldata _chosenNumbers, address _agent) external nonReentrant`**
  - Allows a user to purchase a ticket. Calculates the ticket cost based on the number of chosen numbers and the conversion rate from USD to the native token. Updates the prize pool and agent commissions.

- **`getTicketPriceInNativeToken() public view returns (uint256)`**
  - Returns the price of a ticket in the native token, converted from USD using the Chainlink Price Feed.

- **`checkUpkeep(bytes calldata) external view override returns (bool upkeepNeeded, bytes memory performData)`**
  - Checks if the conditions for performing upkeep are met. Determines if it is time for the next draw and if there are funds in the prize pool.

- **`performUpkeep(bytes calldata) external override`**
  - Requests random numbers from Chainlink VRF if the draw conditions are met.

- **`fulfillRandomWords(uint256, uint256[] memory _randomWords) internal override`**
  - Callback function from Chainlink VRF. Receives random numbers, generates winning numbers, and distributes prizes.

- **`distributePrizes() internal`**
  - Distributes prizes to winning ticket holders and pays out commissions to agents.

- **`getMatchCount(uint8[] memory _chosenNumbers) internal view returns (uint8)`**
  - Counts the number of matches between the chosen numbers and winning numbers.

- **`claimPrize() external nonReentrant`**
  - Allows a player to claim their winnings.

- **`claimAgentCommission() external nonReentrant`**
  - Allows an agent to claim their accumulated commission.

- **`updateTicketPriceUSD(uint256 _newPriceUSD) external onlyRole(UPDATER_ROLE)`**
  - Updates the ticket price in USD. Restricted to users with the `UPDATER_ROLE`.

- **`withdrawFunds(uint256 _amount) external onlyRole(ADMIN_ROLE) nonReentrant`**
  - Allows an admin to withdraw funds from the contract. Restricted to users with the `ADMIN_ROLE`.

- **`grantRole(bytes32 role, address account) public onlyOwner`**
  - Grants a role to an account. Restricted to the contract owner.

- **`revokeRole(bytes32 role, address account) public onlyOwner`**
  - Revokes a role from an account. Restricted to the contract owner.

- **`safeTransfer(IERC20 token, address to, uint256 amount) internal`**
  - Safely transfers tokens from the contract to a specified address.

- **`safeTransferFrom(IERC20 token, address from, address to, uint256 amount) internal`**
  - Safely transfers tokens from one address to the contract.

### Usage

1. **Ticket Purchase:**
   - Users can purchase lottery tickets by calling `purchaseTicket` with their chosen numbers and optionally specifying an agent.

2. **Lottery Draw:**
   - Chainlink Keepers automatically trigger draws at regular intervals. Chainlink VRF ensures randomness in selecting winning numbers.

3. **Claiming Prizes:**
   - Winners can claim their prizes by calling `claimPrize`, while agents can claim their commissions via `claimAgentCommission`.

4. **Role Management:**
   - The contract owner can grant or revoke roles and manage ticket prices.

5. **Fund Management:**
   - Admins can withdraw funds from the contract as needed.

### Security Considerations

- **Reentrancy Protection:**
  - The contract uses `ReentrancyGuard` to protect against reentrant attacks.

- **Access Control:**
  - The `AccessControl` and `Ownable` mechanisms ensure that only authorized users can perform sensitive operations.

- **Chainlink VRF:**
  - Chainlink VRF provides verifiable randomness, which is crucial for ensuring fairness in lottery draws.

- **Token Handling:**
  - The contract uses safe transfer functions to handle ERC20 tokens, reducing the risk of failed transfers or malicious attacks.

This documentation provides a comprehensive overview of the `CryptoDraw` contract, covering its functionality, usage, and security considerations.