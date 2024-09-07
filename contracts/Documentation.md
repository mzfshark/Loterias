
# CryptoDraw Contract Documentation

## Overview

The `CryptoDraw` contract is a decentralized lottery system using Chainlink's VRF (Verifiable Random Function) for generating random numbers and Chainlink's Price Feeds for converting USD to the native token. It allows users to purchase lottery tickets, tracks winning numbers, and manages prize distribution. The contract uses OpenZeppelin's `AccessControl` for role-based access control and `ReentrancyGuard` to prevent reentrancy attacks.

## Components

### State Variables

- **`IERC20 public nativeTokenAddress`**: The address of the ERC20 token used for transactions within the contract.
- **`AggregatorV3Interface public priceFeed`**: Chainlink Price Feed interface to get the USD/NativeToken price.
- **`uint256 public ticketPriceUSD`**: Ticket price in USD (1 USD by default).
- **`uint8 public totalNumbers`**: Total number of numbers available in the lottery.
- **`uint8 public minNumbers`**: Minimum number of chosen numbers required for a ticket.
- **`uint8 public maxNumbers`**: Maximum number of chosen numbers allowed for a ticket.
- **`uint256 public drawInterval`**: Time interval between lottery draws (4 days by default).
- **`uint256 public lastDrawTime`**: Timestamp of the last draw.
- **`uint256 public prizePool`**: Total prize pool accumulated from ticket purchases.
- **`VRFCoordinatorV2Interface COORDINATOR`**: Interface to interact with Chainlink VRF Coordinator.
- **`uint64 public subscriptionId`**: Chainlink VRF subscription ID.
- **`bytes32 public keyHash`**: Key hash for Chainlink VRF.
- **`uint16 requestConfirmations`**: Number of confirmations required for VRF responses.
- **`uint32 callbackGasLimit`**: Gas limit for VRF callback.
- **`uint32 numWords`**: Number of random words requested from Chainlink VRF.
- **`uint256[] public randomWords`**: Array to store random words returned by Chainlink VRF.
- **`uint256 public requestId`**: Request ID for Chainlink VRF.
- **`uint256 public projectFund`**: Funds allocated for project-related expenses.
- **`uint256 public grantFund`**: Funds allocated for grants.
- **`uint256 public operationFund`**: Funds allocated for operational expenses.
- **`struct Ticket`**: Data structure for storing ticket information.
  - `address player`: Address of the ticket holder.
  - `uint8[] chosenNumbers`: Numbers chosen by the player.
  - `bool isElectronic`: Indicates if the ticket was purchased electronically.
  - `address agent`: Address of the agent who sold the ticket.
- **`Ticket[] public tickets`**: Array to store all purchased tickets.
- **`uint8[] public winningNumbers`**: Array to store winning numbers for the draw.
- **`mapping(address => uint256) public winnings`**: Mapping to track winnings for each address.
- **`mapping(address => uint256) public agentCommissions`**: Mapping to track commissions for each agent.

### Events

- **`event TicketPurchased(address indexed player, uint8[] chosenNumbers, address agent, bool isElectronic)`**: Emitted when a ticket is purchased.
- **`event DrawResult(uint8[] winningNumbers)`**: Emitted when a draw result is determined.
- **`event PrizeClaimed(address indexed player, uint256 amount)`**: Emitted when a player claims a prize.
- **`event AgentCommissionPaid(address indexed agent, uint256 amount)`**: Emitted when an agent receives their commission.
- **`event RandomWordsRequested(uint256 requestId)`**: Emitted when a request for random words is made.

### Constructor

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
{
    nativeTokenAddress = IERC20(_nativeTokenAddress);
    COORDINATOR = VRFCoordinatorV2Interface(_vrfCoordinator);
    priceFeed = AggregatorV3Interface(_priceFeedAddress);
    lastDrawTime = block.timestamp;
    keyHash = _keyHash;
    subscriptionId = _subscriptionId;
    projectFund = _initialProjectFund;
    grantFund = _initialGrantFund;
    operationFund = _initialOperationFund;

    // Grant roles to the contract deployer
    _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
    _setupRole(ADMIN_ROLE, msg.sender);
    _setupRole(UPDATER_ROLE, msg.sender);
}
```

- **Parameters**:
  - `_nativeTokenAddress`: Address of the ERC20 token used for the lottery.
  - `_vrfCoordinator`: Address of the Chainlink VRF Coordinator.
  - `_keyHash`: Key hash for Chainlink VRF.
  - `_subscriptionId`: Chainlink VRF subscription ID.
  - `_priceFeedAddress`: Address of the Chainlink Price Feed contract.
  - `_initialProjectFund`: Initial amount allocated for project fund.
  - `_initialGrantFund`: Initial amount allocated for grant fund.
  - `_initialOperationFund`: Initial amount allocated for operational fund.

### Functions

#### `purchaseTicket`

```solidity
function purchaseTicket(uint8[] memory _chosenNumbers, bool _isElectronic, address _agent) external nonReentrant {
    require(_chosenNumbers.length >= minNumbers && _chosenNumbers.length <= maxNumbers, "Invalid number of chosen numbers.");
    
    uint256 ticketPriceInNativeToken = getTicketPriceInNativeToken();
    uint256 ticketCost = ticketPriceInNativeToken * (_chosenNumbers.length - minNumbers + 1);
    safeTransferFrom(nativeTokenAddress, msg.sender, address(this), ticketCost);
    
    tickets.push(Ticket(msg.sender, _chosenNumbers, _isElectronic, _agent));
    prizePool += ticketCost;

    // Calculate and assign agent's commission
    uint256 commission = ticketCost * 861 / 10000; // 8.61% base commission
    if (_isElectronic) {
        commission += ticketCost * 400 / 10000; // Additional 4.00% for electronic sales
    }
    if (_agent != address(0)) {
        agentCommissions[_agent] += commission;
    }

    emit TicketPurchased(msg.sender, _chosenNumbers, _agent, _isElectronic);
}
```

- **Purpose**: Allows users to purchase lottery tickets and pay in native tokens.
- **Parameters**:
  - `_chosenNumbers`: Array of numbers chosen by the player.
  - `_isElectronic`: Boolean indicating if the ticket was purchased electronically.
  - `_agent`: Address of the agent who sold the ticket.
- **Logic**: 
  - Validates the chosen numbers.
  - Converts ticket price from USD to native token.
  - Calculates ticket cost based on chosen numbers.
  - Transfers native tokens from the player to the contract.
  - Adds the ticket to the list and updates the prize pool.
  - Calculates and assigns commission to the agent if applicable.
- **Events**: Emits `TicketPurchased`.

#### `getTicketPriceInNativeToken`

```solidity
function getTicketPriceInNativeToken() public view returns (uint256) {
    (, int256 price, , ,) = priceFeed.latestRoundData();
    require(price > 0, "Invalid price feed data");
    // Convert USD price to nativeToken amount
    uint256 priceInNativeToken = (ticketPriceUSD * 10 ** priceFeed.decimals()) / uint256(price);
    return priceInNativeToken;
}
```

- **Purpose**: Retrieves the price of one ticket in native tokens.
- **Returns**: Ticket price in native tokens.

#### `checkUpkeep`

```solidity
function checkUpkeep(bytes calldata) external view override returns (bool upkeepNeeded, bytes memory performData) {
    upkeepNeeded = (block.timestamp >= lastDrawTime + drawInterval) && (prizePool > 0);
    performData = ""; // Return an empty byte array
}
```

- **Purpose**: Checks if upkeep is needed for the lottery draw.
- **Returns**:
  - `upkeepNeeded`: Boolean indicating if upkeep is needed.
  - `performData`: Empty byte array.

#### `performUpkeep`

```solidity
function performUpkeep(bytes calldata) external override {
    require(block.timestamp >= lastDrawTime + drawInterval, "Draw interval not met.");
    require(prizePool > 0, "No prize pool available.");

    // Request random words from Chainlink VRF
    requestId = COORDINATOR.requestRandomWords(
        keyHash,
        subscriptionId,
        requestConfirmations,
        callbackGasLimit,
        numWords
    );

    emit RandomWordsRequested(requestId);
}
```

- **Purpose**: Requests random words from Chainlink VRF for the lottery draw.
- **Logic**: Validates if the draw interval has passed and if there is a prize pool. Requests random words for the draw.

#### `fulfillRandomWords`

```solidity
function fulfillRandomWords(uint256, uint256[] memory _randomWords) internal override {
    randomWords = _randomWords;
    delete winningNumbers;

    // Generate winning numbers using the

 random words provided by VRF
    for (uint8 i = 0; i < minNumbers; i++) {
        uint8 winningNumber = uint8(_randomWords[i] % totalNumbers) + 1;
        winningNumbers.push(winningNumber);
    }

    lastDrawTime = block.timestamp;
    distributePrizes();

    emit DrawResult(winningNumbers);
}
```

- **Purpose**: Callback function for Chainlink VRF to receive random numbers.
- **Logic**: 
  - Uses random numbers to generate winning numbers.
  - Updates the last draw time.
  - Calls `distributePrizes` to handle prize distribution.

#### `distributePrizes`

```solidity
function distributePrizes() internal {
    // Calculate prize distribution based on breakdowns
    uint256 grossPrize = (prizePool * 4335) / 10000; // 43.35% of the prize pool for the total prize money
    uint256 agentsCommissionTotal = (prizePool * 861) / 10000; // 8.61% for agents' commission

    // Distribute agent commissions
    for (uint256 i = 0; i < tickets.length; i++) {
        if (tickets[i].agent != address(0)) {
            uint256 commission = agentCommissions[tickets[i].agent];
            if (commission > 0) {
                agentCommissions[tickets[i].agent] = 0; // Reset commission after payout
                safeTransfer(nativeTokenAddress, tickets[i].agent, commission);
                emit AgentCommissionPaid(tickets[i].agent, commission);
            }
        }
    }

    // Reset the prize pool after distribution
    prizePool = 0;
}
```

- **Purpose**: Distributes prizes and agent commissions.
- **Logic**: 
  - Calculates and distributes agent commissions.
  - Resets the prize pool after distribution.

#### `getMatchCount`

```solidity
function getMatchCount(uint8[] memory _chosenNumbers) internal view returns (uint8) {
    uint8 matchCount = 0;
    for (uint8 i = 0; i < _chosenNumbers.length; i++) {
        for (uint8 j = 0; j < winningNumbers.length; j++) {
            if (_chosenNumbers[i] == winningNumbers[j]) {
                matchCount++;
                break;
            }
        }
    }
    return matchCount;
}
```

- **Purpose**: Calculates the number of matches between chosen numbers and winning numbers.
- **Returns**: Number of matched numbers.

#### `claimPrize`

```solidity
function claimPrize() external nonReentrant {
    uint256 amount = winnings[msg.sender];
    require(amount > 0, "No winnings to claim.");

    winnings[msg.sender] = 0;
    safeTransfer(nativeTokenAddress, msg.sender, amount);

    emit PrizeClaimed(msg.sender, amount);
}
```

- **Purpose**: Allows users to claim their winnings.
- **Logic**: 
  - Validates if there are winnings to claim.
  - Transfers the winnings to the user's address.
  - Emits `PrizeClaimed`.

#### `claimAgentCommission`

```solidity
function claimAgentCommission() external nonReentrant {
    uint256 amount = agentCommissions[msg.sender];
    require(amount > 0, "No commission to claim.");

    agentCommissions[msg.sender] = 0;
    safeTransfer(nativeTokenAddress, msg.sender, amount);

    emit AgentCommissionPaid(msg.sender, amount);
}
```

- **Purpose**: Allows agents to claim their commissions.
- **Logic**: 
  - Validates if there is a commission to claim.
  - Transfers the commission to the agent's address.
  - Emits `AgentCommissionPaid`.

#### `updateTicketPriceUSD`

```solidity
function updateTicketPriceUSD(uint256 _newPriceUSD) external onlyRole(UPDATER_ROLE) {
    ticketPriceUSD = _newPriceUSD;
}
```

- **Purpose**: Updates the ticket price in USD.
- **Parameters**:
  - `_newPriceUSD`: New ticket price in USD.
- **Access Control**: Restricted to `UPDATER_ROLE`.

#### `withdrawFunds`

```solidity
function withdrawFunds(uint256 _amount) external onlyRole(ADMIN_ROLE) nonReentrant {
    safeTransfer(nativeTokenAddress, msg.sender, _amount);
}
```

- **Purpose**: Allows the admin to withdraw funds from the contract.
- **Parameters**:
  - `_amount`: Amount to withdraw.
- **Access Control**: Restricted to `ADMIN_ROLE`.

#### `grantRole`

```solidity
function grantRole(bytes32 role, address account) public onlyOwner {
    _grantRole(role, account);
}
```

- **Purpose**: Grants a specific role to an address.
- **Parameters**:
  - `role`: Role to grant.
  - `account`: Address to grant the role to.
- **Access Control**: Restricted to contract owner.

#### `revokeRole`

```solidity
function revokeRole(bytes32 role, address account) public onlyOwner {
    _revokeRole(role, account);
}
```

- **Purpose**: Revokes a specific role from an address.
- **Parameters**:
  - `role`: Role to revoke.
  - `account`: Address to revoke the role from.
- **Access Control**: Restricted to contract owner.

#### `safeTransfer`

```solidity
function safeTransfer(IERC20 token, address to, uint256 amount) internal {
    require(token.transfer(to, amount), "Token transfer failed");
}
```

- **Purpose**: Safely transfers tokens.
- **Parameters**:
  - `token`: ERC20 token to transfer.
  - `to`: Address to receive the tokens.
  - `amount`: Amount of tokens to transfer.

#### `safeTransferFrom`

```solidity
function safeTransferFrom(IERC20 token, address from, address to, uint256 amount) internal {
    require(token.transferFrom(from, to, amount), "Token transferFrom failed");
}
```

- **Purpose**: Safely transfers tokens from one address to another.
- **Parameters**:
  - `token`: ERC20 token to transfer.
  - `from`: Address to transfer tokens from.
  - `to`: Address to receive the tokens.
  - `amount`: Amount of tokens to transfer.

## Potential Vulnerabilities and Solutions

### 1. **Reentrancy**

**Concern**: The contract may be vulnerable to reentrancy attacks in functions that handle token transfers.

**Solution**: Use OpenZeppelin's `ReentrancyGuard` and ensure that all state changes occur before making external calls.

### 2. **Arithmetic Overflow/Underflow**

**Concern**: Risk of overflow or underflow in arithmetic operations.

**Solution**: Solidity 0.8.x includes built-in overflow and underflow protection, so explicit SafeMath usage is not necessary.

### 3. **Denial of Service (DoS)**

**Concern**: Functions such as `performUpkeep` could be subjected to DoS attacks if not properly handled.

**Solution**: Ensure that functions with external calls have proper validation and error handling.

### 4. **Access Control**

**Concern**: Sensitive functions like withdrawing funds or updating ticket prices should be restricted to authorized addresses.

**Solution**: Implement role-based access control using OpenZeppelin's `AccessControl` to manage permissions.

### 5. **Gas Costs**

**Concern**: Functions may become expensive in terms of gas, especially with large arrays or complex calculations.

**Solution**: Optimize functions to reduce gas usage and ensure that gas limits are handled appropriately.

### 6. **Contract Upgradeability**

**Concern**: The contract is not upgradeable; any bugs or changes require redeployment.

**Solution**: Consider using a proxy pattern for contract upgradeability if future upgrades are anticipated.

### 7. **Chainlink VRF Failures**

**Concern**: Failures or delays in obtaining random words from Chainlink VRF could affect lottery draws.

**Solution**: Implement retries and handle possible errors in the VRF callback function.

### 8. **Token Transfer Failures**

**Concern**: Token transfers might fail due to various reasons (e.g., insufficient allowance).

**Solution**: Ensure that all token transfers are validated, and errors are handled gracefully.



This documentation provides a comprehensive overview of the `CryptoDraw` contract, its logic, and potential vulnerabilities with suggested solutions. If you need further details or adjustments, feel free to ask!