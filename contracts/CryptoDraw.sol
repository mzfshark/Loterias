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
import "./TicketNFT.sol"; // Import the TicketNFT contract

contract CryptoDraw is VRFConsumerBaseV2, Ownable, KeeperCompatibleInterface, ReentrancyGuard, AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant UPDATER_ROLE = keccak256("UPDATER_ROLE");

    IERC20 public nativeTokenAddress;
    AggregatorV3Interface public priceFeed; // Chainlink Price Feed for USD/NativeToken price
    TicketNFT public ticketNFT; // TicketNFT contract instance
    uint256 public ticketPriceUSD = 1 * 10 ** 18; // Default ticket price in USD (1 USD)
    uint8 public totalNumbers = 25;
    uint8 public minNumbers = 15;
    uint8 public maxNumbers = 20;
    uint256 public drawInterval = 4 days; // Weekly draw interval
    uint256 public lastDrawTime;
    uint256 public prizePool;

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

    // Agents management
    mapping(address => bool) public agents; // Mapping of valid agents
    mapping(address => bool) public isSuspended; // Mapping to track suspended agents
    mapping(address => uint256) public agentTicketCounts; // Count of tickets sold by each agent

    struct Ticket {
        address player;
        uint8[] chosenNumbers;
        address agent; // Agent who sold the ticket
    }

    Ticket[] public tickets;
    uint8[] public winningNumbers;
    mapping(address => uint256) public winnings;
    mapping(address => uint256) public agentCommissions; // Agent commissions tracking

    event TicketPurchased(address indexed player, uint8[] chosenNumbers, address agent);
    event DrawResult(uint8[] winningNumbers);
    event PrizeClaimed(address indexed player, uint256 amount);
    event AgentCommissionPaid(address indexed agent, uint256 amount);
    event RandomWordsRequested(uint256 requestId);
    event AgentAdded(address indexed agent);
    event AgentRemoved(address indexed agent);
    event AgentSuspended(address indexed agent);
    event AgentUnsuspended(address indexed agent);
    event DrawIntervalUpdated(uint256 newDrawInterval); // Event for draw interval update

    constructor(
        address _nativeTokenAddress,
        address _vrfCoordinator,
        bytes32 _keyHash,
        uint64 _subscriptionId,
        address _priceFeedAddress, // Address of the Chainlink Price Feed contract
        address _ticketNFTAddress, // Address of the TicketNFT contract
        uint256 _initialProjectFund,
        uint256 _initialGrantFund,
        uint256 _initialOperationFund
    ) 
        VRFConsumerBaseV2(_vrfCoordinator)
    {
        nativeTokenAddress = IERC20(_nativeTokenAddress);
        COORDINATOR = VRFCoordinatorV2Interface(_vrfCoordinator);
        priceFeed = AggregatorV3Interface(_priceFeedAddress);
        ticketNFT = TicketNFT(_ticketNFTAddress); // Initialize the TicketNFT contract
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

    modifier onlyRole(bytes32 role) {
        require(hasRole(role, msg.sender), "AccessControl: caller does not have the appropriate role");
        _;
    }

    modifier onlyAgent() {
        require(agents[msg.sender], "Caller is not a registered agent");
        _;
    }

    modifier notSuspended() {
        require(!isSuspended[msg.sender], "Agent is suspended");
        _;
    }

    function addAgent(address _agent) external onlyRole(ADMIN_ROLE) {
        require(!agents[_agent], "Agent already added");
        agents[_agent] = true;
        isSuspended[_agent] = false; // Ensure agent is not suspended when added
        emit AgentAdded(_agent);
    }

    function removeAgent(address _agent) external onlyRole(ADMIN_ROLE) {
        require(agents[_agent], "Agent not found");
        agents[_agent] = false;
        isSuspended[_agent] = false; // Ensure agent is not suspended when removed
        emit AgentRemoved(_agent);
    }

    function suspendAgent(address _agent) external onlyRole(ADMIN_ROLE) {
        require(agents[_agent], "Agent not found");
        isSuspended[_agent] = true;
        emit AgentSuspended(_agent);
    }

    function unsuspendAgent(address _agent) external onlyRole(ADMIN_ROLE) {
        require(agents[_agent], "Agent not found");
        isSuspended[_agent] = false;
        emit AgentUnsuspended(_agent);
    }

    function updateDrawInterval(uint256 _newDrawInterval) external onlyRole(ADMIN_ROLE) {
        drawInterval = _newDrawInterval;
        emit DrawIntervalUpdated(_newDrawInterval);
    }

    function purchaseTicket(uint8[] calldata _chosenNumbers, address _agent) external nonReentrant notSuspended {
        require(agents[_agent], "Invalid agent address");
        require(!isSuspended[_agent], "Agent is suspended");
        require(_chosenNumbers.length >= minNumbers && _chosenNumbers.length <= maxNumbers, "Invalid number of chosen numbers.");
        
        uint256 ticketPriceInNativeToken = getTicketPriceInNativeToken();
        uint256 ticketCost = ticketPriceInNativeToken * (_chosenNumbers.length - minNumbers + 1);
        safeTransferFrom(nativeTokenAddress, msg.sender, address(this), ticketCost);

        // Mint NFT for the ticket
        uint256 tokenId = ticketNFT.mint(msg.sender, _chosenNumbers);

        tickets.push(Ticket(msg.sender, _chosenNumbers, _agent));
        agentTicketCounts[_agent] += 1; // Track tickets sold by the agent
        prizePool += ticketCost;

        // Calculate and assign agent's commission
        uint256 commission = ticketCost * 861 / 10000; // 8.61% base commission
        if (_agent != address(0)) {
            agentCommissions[_agent] += commission;
        }

        emit TicketPurchased(msg.sender, _chosenNumbers, _agent);
    }

    function getTicketPriceInNativeToken() public view returns (uint256) {
        (, int256 price, , ,) = priceFeed.latestRoundData();
        require(price > 0, "Invalid price feed data");
        // Convert USD price to nativeToken amount
        uint256 priceInNativeToken = (ticketPriceUSD * 10 ** priceFeed.decimals()) / uint256(price);
        return priceInNativeToken;
    }

    function checkUpkeep(bytes calldata) external view override returns (bool upkeepNeeded, bytes memory performData) {
        upkeepNeeded = (block.timestamp >= lastDrawTime + drawInterval) && (prizePool > 0);
        performData = ""; // Return an empty byte array
    }

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

    // Callback function called by Chainlink VRF Coordinator
    function fulfillRandomWords(uint256, uint256[] memory _randomWords) internal override {
        randomWords = _randomWords;
        delete winningNumbers;

        // Generate winning numbers using the random words provided by VRF
        for (uint8 i = 0; i < minNumbers; i++) {
            uint8 winningNumber = uint8(_randomWords[i] % totalNumbers) + 1;
            winningNumbers.push(winningNumber);
        }

        lastDrawTime = block.timestamp;
        distributePrizes();

        emit DrawResult(winningNumbers);
    }

    function distributePrizes() internal {
        // Calculate prize distribution based on breakdowns
        uint256 grossPrize = (prizePool * 4335) / 10000; // 43.35% of the prize pool for the total prize money
        uint256 agentsCommissionTotal = (prizePool * 861) / 10000; // 8.61% for agents' commission

        // Distribute agent commissions
        for (uint256 i = 0; i < tickets.length; i++) {
            address agent = tickets[i].agent;
            if (agent != address(0) && !isSuspended[agent]) {
                uint256 commission = agentCommissions[agent];
                if (commission > 0) {
                    agentCommissions[agent] = 0; // Reset commission after payout
                    safeTransfer(nativeTokenAddress, agent, commission);
                    emit AgentCommissionPaid(agent, commission);
                }
            }
        }

        // Reset the prize pool after distribution
        prizePool = 0;
    }

    function getMatchCount(uint8[] memory _chosenNumbers) internal view returns (uint8) {
        uint8 matchCount = 0;
        mapping(uint8 => bool) memory winningNumbersMap;

        // Store winning numbers in a mapping for faster lookup
        for (uint8 i = 0; i < winningNumbers.length; i++) {
            winningNumbersMap[winningNumbers[i]] = true;
        }

        // Check for matches
        for (uint8 i = 0; i < _chosenNumbers.length; i++) {
            if (winningNumbersMap[_chosenNumbers[i]]) {
                matchCount++;
            }
        }

        return matchCount;
    }

    function claimPrize() external nonReentrant {
        uint256 amount = winnings[msg.sender];
        require(amount > 0, "No winnings to claim.");

        winnings[msg.sender] = 0;
        safeTransfer(nativeTokenAddress, msg.sender, amount);

        emit PrizeClaimed(msg.sender, amount);
    }

    function claimAgentCommission() external nonReentrant {
        uint256 amount = agentCommissions[msg.sender];
        require(amount > 0, "No commission to claim.");
        require(!isSuspended[msg.sender], "Agent is suspended");

        agentCommissions[msg.sender] = 0;
        safeTransfer(nativeTokenAddress, msg.sender, amount);

        emit AgentCommissionPaid(msg.sender, amount);
    }

    function updateTicketPriceUSD(uint256 _newPriceUSD) external onlyRole(UPDATER_ROLE) {
        ticketPriceUSD = _newPriceUSD;
    }

    function withdrawFunds(uint256 _amount) external onlyRole(ADMIN_ROLE) nonReentrant {
        safeTransfer(nativeTokenAddress, msg.sender, _amount);
    }

    function grantRole(bytes32 role, address account) public onlyOwner {
        _grantRole(role, account);
    }

    function revokeRole(bytes32 role, address account) public onlyOwner {
        _revokeRole(role, account);
    }

    function getAgentTicketCount(address _agent) external view returns (uint256) {
        return agentTicketCounts[_agent];
    }

    function safeTransfer(IERC20 token, address to, uint256 amount) internal {
        uint256 balance = token.balanceOf(address(this));
        require(balance >= amount, "Insufficient balance");
        require(token.transfer(to, amount), "Token transfer failed");
    }

    function safeTransferFrom(IERC20 token, address from, address to, uint256 amount) internal {
        uint256 balance = token.balanceOf(from);
        require(balance >= amount, "Insufficient balance");
        require(token.transferFrom(from, to, amount), "Token transferFrom failed");
    }
}
