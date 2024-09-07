// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/vrf/VRFConsumerBaseV2.sol";
import "@chainlink/contracts/src/v0.8/vrf/interfaces/VRFCoordinatorV2Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.8/automation/interfaces/KeeperCompatibleInterface.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@chainlink/contracts/src/v0.8/shared/interfaces/AggregatorV3Interface.sol";

contract LottoChain is VRFConsumerBaseV2, Ownable, KeeperCompatibleInterface, ReentrancyGuard {
    IERC20 public nativeTokenAddress;
    AggregatorV3Interface public priceFeed; // Chainlink Price Feed for USD/NativeToken price
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
    uint32 callbackGasLimit = 100000; // Adjust according to your requirements
    uint32 numWords = 15; // Number of random numbers needed (15 winning numbers)
    uint256[] public randomWords;
    uint256 public requestId;

    // Funds for various uses
    uint256 public projectFund;
    uint256 public grantFund;
    uint256 public operationFund;

    struct Ticket {
        address player;
        uint8[] chosenNumbers;
        bool isElectronic; // True if the ticket was sold on an electronic channel
        address agent; // Agent who sold the ticket
    }

    Ticket[] public tickets;
    uint8[] public winningNumbers;
    mapping(address => uint256) public winnings;
    mapping(address => uint256) public agentCommissions; // Agent commissions tracking

    event TicketPurchased(address indexed player, uint8[] chosenNumbers, address agent, bool isElectronic);
    event DrawResult(uint8[] winningNumbers);
    event PrizeClaimed(address indexed player, uint256 amount);
    event AgentCommissionPaid(address indexed agent, uint256 amount);
    event RandomWordsRequested(uint256 requestId);

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
    }

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

        agentCommissions[msg.sender] = 0;
        safeTransfer(nativeTokenAddress, msg.sender, amount);

        emit AgentCommissionPaid(msg.sender, amount);
    }

    function updateTicketPriceUSD(uint256 _newPriceUSD) external onlyOwner {
        ticketPriceUSD = _newPriceUSD;
    }

    function withdrawFunds(uint256 _amount) external onlyOwner nonReentrant {
        safeTransfer(nativeTokenAddress, msg.sender, _amount);
    }

    function safeTransfer(IERC20 token, address to, uint256 amount) internal {
        require(token.transfer(to, amount), "Token transfer failed");
    }

    function safeTransferFrom(IERC20 token, address from, address to, uint256 amount) internal {
        require(token.transferFrom(from, to, amount), "Token transferFrom failed");
    }
}
