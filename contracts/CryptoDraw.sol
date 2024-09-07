// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/vrf/VRFConsumerBaseV2.sol";
import "@chainlink/contracts/src/v0.8/vrf/interfaces/VRFCoordinatorV2Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@chainlink/contracts/src/v0.8/automation/interfaces/KeeperCompatibleInterface.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@chainlink/contracts/src/v0.8/shared/interfaces/AggregatorV3Interface.sol";
import "./TicketNFT.sol";

contract CryptoDraw is VRFConsumerBaseV2, Ownable, KeeperCompatibleInterface, ReentrancyGuard, AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant UPDATER_ROLE = keccak256("UPDATER_ROLE");

    IERC20 public nativeTokenAddress;
    AggregatorV3Interface public priceFeed; // Chainlink Price Feed for USD/NativeToken price
    uint256 public ticketPriceUSD = 1 * 10 ** 18; // Default ticket price in USD (1 USD)
    uint8 public totalNumbers = 25;
    uint8 public minNumbers = 15;
    uint8 public maxNumbers = 20;
    uint256 public drawInterval = 4 days; // Weekly draw interval
    uint256 public lastDrawTime;
    uint256 public prizePool;
    uint256 public drawRound = 1; // Initialize draw round to 1

    // Chainlink VRF Variables
    VRFCoordinatorV2Interface COORDINATOR;
    uint64 public subscriptionId;
    bytes32 public keyHash;
    uint16 requestConfirmations = 3;
    uint32 callbackGasLimit = 50000; // Adjust according to your requirements
    uint32 numWords = 15; // Number of random numbers needed (15 winning numbers)
    uint256[] public randomWords;
    uint256 public requestId;

    // Funds for various uses
    uint256 public projectFund;
    uint256 public grantFund;
    uint256 public operationFund;

    // Contract state
    bool public paused = false;
    uint256 public pauseDuration = 2 hours; // 2 hours before the draw

    struct Ticket {
        address player;
        uint8[] chosenNumbers;
        address agent; // Agent who sold the ticket
        uint256 round; // Draw round in which the ticket was purchased
        bool valid; // Flag to indicate if the ticket is still valid
    }

    Ticket[] public tickets;
    mapping(uint256 => uint8[]) public roundWinningNumbers; // Store winning numbers by round
    mapping(address => uint256) public winnings;
    mapping(address => uint256) public agentCommissions; // Agent commissions tracking
    mapping(address => bool) public agentStatus; // Agent status tracking
    mapping(address => mapping(uint256 => uint8)) public agentTicketsSold; // Tracking tickets sold by agents

    event TicketPurchased(address indexed player, uint8[] chosenNumbers, address agent, uint256 round);
    event DrawResult(uint8[] winningNumbers, uint256 round);
    event PrizeClaimed(address indexed player, uint256 amount);
    event AgentCommissionPaid(address indexed agent, uint256 amount);
    event RandomWordsRequested(uint256 requestId);
    event ContractPaused();
    event ContractUnpaused();

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
        lastDrawTime = getNextDrawTime();
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

    modifier onlyRole(bytes32 role) override {
        require(hasRole(role, msg.sender), "AccessControl: caller does not have the appropriate role");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    function getNextDrawTime() public view returns (uint256) {
        uint256 currentTime = block.timestamp;
        uint256 secondsSinceStartOfDay = (currentTime % 1 days);
        uint256 secondsUntilNextMidnight = (1 days - secondsSinceStartOfDay);
        return currentTime + secondsUntilNextMidnight;
    }

    function purchaseTicket(uint8[] calldata _chosenNumbers, address _agent) external nonReentrant whenNotPaused {
        require(_chosenNumbers.length >= minNumbers && _chosenNumbers.length <= maxNumbers, "Invalid number of chosen numbers.");
        require(agentStatus[_agent], "Agent is not active.");
        require(block.timestamp < (getNextDrawTime() - pauseDuration), "Ticket purchases are paused.");

        uint256 ticketPriceInNativeToken = getTicketPriceInNativeToken();
        uint256 ticketCost = ticketPriceInNativeToken * (_chosenNumbers.length - minNumbers + 1);
        safeTransferFrom(nativeTokenAddress, msg.sender, address(this), ticketCost);

        tickets.push(Ticket({
            player: msg.sender,
            chosenNumbers: _chosenNumbers,
            agent: _agent,
            round: drawRound,
            valid: true
        }));
        prizePool += ticketCost;

        // Calculate and assign agent's commission
        uint256 commission = ticketCost * 861 / 10000; // 8.61% base commission
        if (_agent != address(0)) {
            agentCommissions[_agent] += commission;
            agentTicketsSold[_agent][drawRound] += 1;
        }

        emit TicketPurchased(msg.sender, _chosenNumbers, _agent, drawRound);
    }

    function getTicketPriceInNativeToken() public view returns (uint256) {
        (, int256 price, , ,) = priceFeed.latestRoundData();
        require(price > 0, "Invalid price feed data");
        // Convert USD price to nativeToken amount
        uint256 priceInNativeToken = (ticketPriceUSD * 10 ** priceFeed.decimals()) / uint256(price);
        return priceInNativeToken;
    }

    function checkUpkeep(bytes calldata) external view override returns (bool upkeepNeeded, bytes memory performData) {
        upkeepNeeded = (block.timestamp >= lastDrawTime) && (prizePool > 0);
        performData = ""; // Return an empty byte array
    }

    function performUpkeep(bytes calldata) external override {
        require(block.timestamp >= lastDrawTime, "Draw time not reached.");
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

    // Callback function called by Chainlink VRF Coordinator
    function fulfillRandomWords(uint256, uint256[] memory _randomWords) internal override {
        randomWords = _randomWords;
        delete roundWinningNumbers[drawRound];

        // Generate winning numbers using the random words provided by VRF
        for (uint8 i = 0; i < minNumbers; i++) {
            uint8 winningNumber = uint8(_randomWords[i] % totalNumbers) + 1;
            roundWinningNumbers[drawRound].push(winningNumber);
        }

        lastDrawTime = getNextDrawTime(); // Schedule next draw
        distributePrizes();

        emit DrawResult(roundWinningNumbers[drawRound], drawRound);

        // Increment draw round for the next draw
        drawRound++;
    }

    function distributePrizes() internal {
        uint256 grossPrize = (prizePool * 4335) / 10000; // 43.35% of the prize pool for the total prize money
        uint256 agentsCommissionTotal = (prizePool * 861) / 10000; // 8.61% for agents' commission

        // Distribute agent commissions
        for (uint256 i = 0; i < tickets.length; i++) {
            if (tickets[i].agent != address(0) && agentStatus[tickets[i].agent] && tickets[i].valid) {
                uint256 commission = agentCommissions[tickets[i].agent];
                if (commission > 0) {
                    agentCommissions[tickets[i].agent] = 0; // Reset commission after payout
                    safeTransfer(nativeTokenAddress, tickets[i].agent, commission);
                    emit AgentCommissionPaid(tickets[i].agent, commission);
                }
            }
        }

        // Calculate and distribute prizes to players
        for (uint256 i = 0; i < tickets.length; i++) {
            if (tickets[i].player != address(0) && tickets[i].valid) {
                uint8 matchCount = getMatchCount(tickets[i].chosenNumbers, roundWinningNumbers[drawRound]);
                uint256 prize = (grossPrize * matchCount) / minNumbers; // Simplified prize calculation
                if (prize > 0) {
                    winnings[tickets[i].player] += prize;
                }
            }
        }
        prizePool = 0; // Reset prize pool after distribution
    }

    function getMatchCount(uint8[] memory _chosenNumbers, uint8[] memory _winningNumbers) internal pure returns (uint8) {
        uint8 matchCount = 0;
        mapping(uint8 => bool) memory winningNumbersMap;
        for (uint8 i = 0; i < _winningNumbers.length; i++) {
            winningNumbersMap[_winningNumbers[i]] = true;
        }
        for (uint8 i = 0; i < _chosenNumbers.length; i++) {
            if (winningNumbersMap[_chosenNumbers[i]]) {
                matchCount++;
            }
        }
        return matchCount;
    }

    function claimPrize() external nonReentrant {
        uint256 totalWinnings = winnings[msg.sender];
        require(totalWinnings > 0, "No winnings to claim.");

        winnings[msg.sender] = 0; // Reset winnings
        safeTransfer(nativeTokenAddress, msg.sender, totalWinnings);

        // Burn winning tickets
        for (uint256 i = 0; i < tickets.length; i++) {
            if (tickets[i].player == msg.sender && tickets[i].round < drawRound && tickets[i].valid) {
                tickets[i].valid = false; // Invalidate the ticket
            }
        }

        emit PrizeClaimed(msg.sender, totalWinnings);
    }

    function setDrawInterval(uint256 _interval) external onlyRole(ADMIN_ROLE) {
        drawInterval = _interval;
    }

    function setTicketPrice(uint256 _priceUSD) external onlyRole(ADMIN_ROLE) {
        ticketPriceUSD = _priceUSD * 10 ** 18; // Convert to 18 decimal places
    }

    function setAgentStatus(address _agent, bool _status) external onlyRole(ADMIN_ROLE) {
        agentStatus[_agent] = _status;
    }

    function pauseContract() external onlyRole(ADMIN_ROLE) {
        paused = true;
        emit ContractPaused();
    }

    function unpauseContract() external onlyRole(ADMIN_ROLE) {
        paused = false;
        emit ContractUnpaused();
    }

    function getAgentCommission(address _agent) external view returns (uint256) {
        return agentCommissions[_agent];
    }

    function getTicket(uint256 ticketId) external view returns (Ticket memory) {
        require(ticketId < tickets.length, "Invalid ticket ID");
        return tickets[ticketId];
    }

    function safeTransfer(IERC20 token, address to, uint256 amount) internal {
        require(token.transfer(to, amount), "Transfer failed");
    }

    function safeTransferFrom(IERC20 token, address from, address to, uint256 amount) internal {
        require(token.transferFrom(from, to, amount), "Transfer failed");
    }
}
