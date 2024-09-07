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

contract CryptoDraw is VRFConsumerBaseV2, Ownable, KeeperCompatibleInterface, ReentrancyGuard, AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant UPDATER_ROLE = keccak256("UPDATER_ROLE");

    IERC20 public nativeTokenAddress;
    AggregatorV3Interface public priceFeed;
    uint256 public ticketPriceUSD = 1 * 10 ** 18;
    uint8 public totalNumbers = 25;
    uint8 public minNumbers = 15;
    uint8 public maxNumbers = 20;
    uint256 public drawInterval = 4 days;
    uint256 public lastDrawTime;
    uint256 public prizePool;
    uint256 public currentDrawRound;
    bool public paused = false;

    // Chainlink VRF Variables
    VRFCoordinatorV2Interface COORDINATOR;
    uint64 public subscriptionId;
    bytes32 public keyHash;
    uint16 requestConfirmations = 3;
    uint32 callbackGasLimit = 50000;
    uint32 numWords = 15;
    uint256[] public randomWords;
    uint256 public requestId;

    // Funds for various uses
    uint256 public projectFund;
    uint256 public grantFund;
    uint256 public operationFund;

    struct Ticket {
        address player;
        uint8[] chosenNumbers;
        address agent;
        uint256 drawRound;
    }

    Ticket[] public tickets;
    uint8[] public winningNumbers;
    mapping(address => uint256) public winnings;
    mapping(address => uint256) public agentCommissions;
    mapping(address => bool) public agents;
    mapping(address => bool) public agentSuspended;

    event TicketPurchased(address indexed player, uint8[] chosenNumbers, address agent);
    event DrawResult(uint8[] winningNumbers);
    event PrizeClaimed(address indexed player, uint256 amount);
    event AgentCommissionPaid(address indexed agent, uint256 amount);
    event RandomWordsRequested(uint256 requestId);
    event Paused();
    event Unpaused();

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
        currentDrawRound = 1;

        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(ADMIN_ROLE, msg.sender);
        _setupRole(UPDATER_ROLE, msg.sender);
    }

    modifier onlyRole(bytes32 role) {
        require(hasRole(role, msg.sender), "AccessControl: caller does not have the appropriate role");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    modifier onlyAgent() {
        require(agents[msg.sender] && !agentSuspended[msg.sender], "Not an active agent");
        _;
    }

    function purchaseTicket(uint8[] calldata _chosenNumbers, address _agent) external nonReentrant whenNotPaused {
        require(_chosenNumbers.length >= minNumbers && _chosenNumbers.length <= maxNumbers, "Invalid number of chosen numbers.");
        require(block.timestamp < lastDrawTime + drawInterval - 2 hours, "Purchases paused.");

        uint256 ticketPriceInNativeToken = getTicketPriceInNativeToken();
        uint256 ticketCost = ticketPriceInNativeToken * (_chosenNumbers.length - minNumbers + 1);
        safeTransferFrom(nativeTokenAddress, msg.sender, address(this), ticketCost);

        tickets.push(Ticket(msg.sender, _chosenNumbers, _agent, currentDrawRound));
        prizePool += ticketCost;

        uint256 commission = ticketCost * 861 / 10000;
        if (_agent != address(0) && !agentSuspended[_agent]) {
            agentCommissions[_agent] += commission;
        }

        emit TicketPurchased(msg.sender, _chosenNumbers, _agent);
    }

    function getTicketPriceInNativeToken() public view returns (uint256) {
        (, int256 price, , ,) = priceFeed.latestRoundData();
        require(price > 0, "Invalid price feed data");
        uint256 priceInNativeToken = (ticketPriceUSD * 10 ** priceFeed.decimals()) / uint256(price);
        return priceInNativeToken;
    }

    function checkUpkeep(bytes calldata) external view override returns (bool upkeepNeeded, bytes memory performData) {
        bool drawTimeReached = (block.timestamp >= getNextDrawTime() && block.timestamp < getNextDrawTime() + 1 hours);
        upkeepNeeded = !paused && drawTimeReached && prizePool > 0;
        performData = "";
    }

    function performUpkeep(bytes calldata) external override whenNotPaused {
        require(block.timestamp >= getNextDrawTime(), "Draw time not reached.");
        require(prizePool > 0, "No prize pool available.");

        requestId = COORDINATOR.requestRandomWords(
            keyHash,
            subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            numWords
        );

        emit RandomWordsRequested(requestId);
    }

    function fulfillRandomWords(uint256, uint256[] memory _randomWords) internal override {
        randomWords = _randomWords;
        delete winningNumbers;

        for (uint8 i = 0; i < minNumbers; i++) {
            uint8 winningNumber = uint8(_randomWords[i] % totalNumbers) + 1;
            winningNumbers.push(winningNumber);
        }

        lastDrawTime = block.timestamp;
        currentDrawRound++;
        distributePrizes();

        emit DrawResult(winningNumbers);
    }

    function distributePrizes() internal {
        uint256 grossPrize = (prizePool * 4335) / 10000;
        uint256 agentsCommissionTotal = (prizePool * 861) / 10000;

        for (uint256 i = 0; i < tickets.length; i++) {
            if (tickets[i].agent != address(0) && !agentSuspended[tickets[i].agent]) {
                uint256 commission = agentCommissions[tickets[i].agent];
                if (commission > 0) {
                    agentCommissions[tickets[i].agent] = 0;
                    safeTransfer(nativeTokenAddress, tickets[i].agent, commission);
                    emit AgentCommissionPaid(tickets[i].agent, commission);
                }
            }

            uint8 matchCount = getMatchCount(tickets[i].chosenNumbers);
            if (matchCount >= minNumbers) {
                uint256 prizeAmount = grossPrize / tickets.length;
                winnings[tickets[i].player] += prizeAmount;

                // Burn the NFT here
                // Assuming a function `burnNFT` exists in the TicketNFT contract
                // ticketNFT.burn(ticketId); 
            }
        }

        prizePool = 0;
    }

    function getMatchCount(uint8[] memory _chosenNumbers) internal view returns (uint8) {
        uint8 matchCount = 0;
        bool[26] memory winningNumbersSet;

        for (uint8 i = 0; i < winningNumbers.length; i++) {
            winningNumbersSet[winningNumbers[i] - 1] = true;
        }

        for (uint8 i = 0; i < _chosenNumbers.length; i++) {
            if (winningNumbersSet[_chosenNumbers[i] - 1]) {
                matchCount++;
            }
        }

        return matchCount;
    }

    function claimPrize() external nonReentrant whenNotPaused {
        uint256 amount = winnings[msg.sender];
        require(amount > 0, "No winnings to claim.");

        winnings[msg.sender] = 0;
        safeTransfer(nativeTokenAddress, msg.sender, amount);

        emit PrizeClaimed(msg.sender, amount);
    }

    function claimAgentCommission() external nonReentrant whenNotPaused {
        uint256 amount = agentCommissions[msg.sender];
        require(amount > 0, "No commission to claim.");

        agentCommissions[msg.sender] = 0;
        safeTransfer(nativeTokenAddress, msg.sender, amount);

        emit AgentCommissionPaid(msg.sender, amount);
    }

    function pause() external onlyRole(ADMIN_ROLE) {
        paused = true;
        emit Paused();
    }

    function unpause() external onlyRole(ADMIN_ROLE) {
        paused = false;
        emit Unpaused();
    }

    function getNextDrawTime() public view returns (uint256) {
        return lastDrawTime + drawInterval;
    }

    function setDrawInterval(uint256 _drawInterval) external onlyRole(ADMIN_ROLE) {
        drawInterval = _drawInterval;
    }

    function setTicketPriceUSD(uint256 _ticketPriceUSD) external onlyRole(ADMIN_ROLE) {
        ticketPriceUSD = _ticketPriceUSD;
    }

    function addAgent(address _agent) external onlyRole(ADMIN_ROLE) {
        agents[_agent] = true;
    }

    function removeAgent(address _agent) external onlyRole(ADMIN_ROLE) {
        agents[_agent] = false;
        agentSuspended[_agent] = false; // Unsuspend if currently suspended
    }

    function suspendAgent(address _agent) external onlyRole(ADMIN_ROLE) {
        agentSuspended[_agent] = true;
    }

    function unsuspendAgent(address _agent) external onlyRole(ADMIN_ROLE) {
        agentSuspended[_agent] = false;
    }

    function safeTransfer(IERC20 token, address to, uint256 amount) internal {
        require(token.transfer(to, amount), "Transfer failed");
    }

    function safeTransferFrom(IERC20 token, address from, address to, uint256 amount) internal {
        require(token.transferFrom(from, to, amount), "TransferFrom failed");
    }
}
