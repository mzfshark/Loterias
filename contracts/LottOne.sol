// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/vrf/VRFConsumerBaseV2.sol";
import "@chainlink/contracts/src/v0.8/vrf/interfaces/VRFCoordinatorV2Interface.sol";

contract LottOne is VRFConsumerBaseV2 {
    IERC20 public oneToken;
    address public owner;
    uint256 public ticketPrice = 1 * 10 ** 18; // Base price in ONE tokens (adjust as necessary)
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

    constructor(address _oneToken, address _vrfCoordinator, bytes32 _keyHash, uint64 _subscriptionId) 
        VRFConsumerBaseV2(_vrfCoordinator) 
    {
        oneToken = IERC20(_oneToken);
        COORDINATOR = VRFCoordinatorV2Interface(_vrfCoordinator);
        owner = msg.sender;
        lastDrawTime = block.timestamp;
        keyHash = _keyHash;
        subscriptionId = _subscriptionId;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function.");
        _;
    }

    function purchaseTicket(uint8[] memory _chosenNumbers, bool _isElectronic, address _agent) external {
        require(_chosenNumbers.length >= minNumbers && _chosenNumbers.length <= maxNumbers, "Invalid number of chosen numbers.");
        
        uint256 ticketCost = ticketPrice * (_chosenNumbers.length - minNumbers + 1);
        require(oneToken.transferFrom(msg.sender, address(this), ticketCost), "Token transfer failed.");
        
        tickets.push(Ticket(msg.sender, _chosenNumbers, _isElectronic, _agent));
        prizePool += ticketCost;

        // Calculate and assign agent's commission
        uint256 commission = ticketCost * 861 / 10000; // 8.61% base commission
        if (_isElectronic) {
            commission += ticketCost * 400 / 10000; // Additional 4.00% for electronic sales
        }
        agentCommissions[_agent] += commission;

        emit TicketPurchased(msg.sender, _chosenNumbers, _agent, _isElectronic);
    }

    function draw() external onlyOwner {
        require(block.timestamp >= lastDrawTime + drawInterval, "Draw interval not met.");

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
        // Calculate distributions according to the revised breakdown
        uint256 grossPrize = prizePool * 4335 / 10000; // 43.35%
        uint256 agentsCommissionTotal = prizePool * 861 / 10000; // 8.61%
        uint256 developmentFund = prizePool * 95 / 10000; // 0.95%
        uint256 operationalExpenses = prizePool * 957 / 10000; // 9.57%

        // Calculate remaining amount
        uint256 remainingAmount = prizePool - (grossPrize + agentsCommissionTotal + developmentFund + operationalExpenses);

        // Further breakdown of the remaining amount
        uint256 recoveryOneProgram = remainingAmount * 75 / 100; // 75% of remaining
        uint256 grantFund = remainingAmount * 20 / 100; // 20% of remaining
        uint256 otherOperationInvestments = remainingAmount * 5 / 100; // 5% of remaining

        // Example prize pool distribution
        uint256 jackpotShare = grossPrize * 50 / 100; // 50% for jackpot
        uint256 significantShare = grossPrize * 30 / 100; // 30% for significant prize
        uint256 smallerPrizePool = grossPrize * 20 / 100; // 20% for smaller prizes

        uint256 matched15 = 0;
        uint256 matched14 = 0;
        uint256 matched13 = 0;
        uint256 matched12 = 0;
        uint256 matched11 = 0;

        for (uint256 i = 0; i < tickets.length; i++) {
            uint8 matchCount = getMatchCount(tickets[i].chosenNumbers);
            if (matchCount == 15) {
                matched15++;
                winnings[tickets[i].player] += jackpotShare / matched15;
            } else if (matchCount == 14) {
                matched14++;
                winnings[tickets[i].player] += significantShare / matched14;
            } else if (matchCount >= 11) {
                uint256 prize = smallerPrizePool / (matched13 + matched12 + matched11);
                winnings[tickets[i].player] += prize;
            }
        }

        prizePool = 0; // Reset prize pool after distribution
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

    function claimPrize() external {
        uint256 amount = winnings[msg.sender];
        require(amount > 0, "No winnings to claim.");

        winnings[msg.sender] = 0;
        require(oneToken.transfer(msg.sender, amount), "Token transfer failed.");

        emit PrizeClaimed(msg.sender, amount);
    }

    function claimAgentCommission() external {
        uint256 amount = agentCommissions[msg.sender];
        require(amount > 0, "No commission to claim.");

        agentCommissions[msg.sender] = 0;
        require(oneToken.transfer(msg.sender, amount), "Token transfer failed.");

        emit AgentCommissionPaid(msg.sender, amount);
    }

    function updateTicketPrice(uint256 _newPrice) external onlyOwner {
        ticketPrice = _newPrice;
    }

    function withdrawFunds(uint256 _amount) external onlyOwner {
        require(oneToken.transfer(owner, _amount), "Token transfer failed.");
    }
}
