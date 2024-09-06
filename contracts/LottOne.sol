// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/vrf/VRFConsumerBaseV2.sol";
import "@chainlink/contracts/src/v0.8/vrf/interfaces/VRFCoordinatorV2Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.8/interfaces/KeeperCompatibleInterface.sol";

contract LottOne is VRFConsumerBaseV2, Ownable, KeeperCompatibleInterface {
    IERC20 public oneToken;
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

    constructor(address _oneToken, address _vrfCoordinator, bytes32 _keyHash, uint64 _subscriptionId, uint256 _projectFund, uint256 _grantFund, uint256 _operationFund) 
        VRFConsumerBaseV2(_vrfCoordinator) 
    {
        oneToken = IERC20(_oneToken);
        COORDINATOR = VRFCoordinatorV2Interface(_vrfCoordinator);
        lastDrawTime = block.timestamp;
        keyHash = _keyHash;
        subscriptionId = _subscriptionId;
        projectFund = _projectFund;
        grantFund = _grantFund;
        operationFund = _operationFund;
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

    function checkUpkeep(bytes calldata) external view override returns (bool upkeepNeeded, bytes memory) {
        upkeepNeeded = (block.timestamp >= lastDrawTime + drawInterval) && (prizePool > 0);
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
        // Calculate distributions according to the revised breakdown
        uint256 grossPrize = (prizePool * 4335) / 10000; // 43.35% of the prize pool for the total prize money
        uint256 agentsCommissionTotal = (prizePool * 861) / 10000; // 8.61% for agents' commission
        uint256 developmentFund = (prizePool * 95) / 10000; // 0.95% for lottery development fund (FDL)
        uint256 operationalExpenses = (prizePool * 957) / 10000; // 9.57% for operational expenses
        uint256 chainHealthInvestment = (prizePool * 2496) / 10000; // 24.96% for Chain Health Investment Program
        uint256 grantFund = (prizePool * 772) / 10000; // 7.72% for grant fund
        uint256 operationFund = (prizePool * 493) / 10000; // 4.93% for operation fund

        // Deduct total agent commissions from the prize pool
        uint256 adjustedPrizePool = prizePool - agentsCommissionTotal;

        // Calculate prize distribution for winners
        uint256 jackpotShare = (grossPrize * 7600) / 10000; // 76% for jackpot winners
        uint256 shareMatched14 = (grossPrize * 1400) / 10000; // 14% for 14 matches
        uint256 shareMatched13 = (grossPrize * 500) / 10000; // 5% for 13 matches
        uint256 shareMatched12 = (grossPrize * 300) / 10000; // 3% for 12 matches
        uint256 shareMatched11 = (grossPrize * 200) / 10000; // 2% for 11 matches

        uint256 matched15 = 0;
        uint256 matched14 = 0;
        uint256 matched13 = 0;
        uint256 matched12 = 0;
        uint256 matched11 = 0;

        // Count matches for each prize level
        for (uint256 i = 0; i < tickets.length; i++) {
            uint8 matchCount = getMatchCount(tickets[i].chosenNumbers);
            if (matchCount == 15) {
                matched15++;
            } else if (matchCount == 14) {
                matched14++;
            } else if (matchCount == 13) {
                matched13++;
            } else if (matchCount == 12) {
                matched12++;
            } else if (matchCount == 11) {
                matched11++;
            }
        }

        // Distribute agent commissions
        for (uint256 i = 0; i < tickets.length; i++) {
            if (tickets[i].agent != address(0)) {
                uint256 commission = agentCommissions[tickets[i].agent];
                if (commission > 0) {
                    agentCommissions[tickets[i].agent] = 0; // Reset commission after payout
                    require(oneToken.transfer(tickets[i].agent, commission), "Token transfer failed.");
                    emit AgentCommissionPaid(tickets[i].agent, commission);
                }
            }
        }

        // Distribute prizes proportionally among winners
        for (uint256 i = 0; i < tickets.length; i++) {
            uint8 matchCount = getMatchCount(tickets[i].chosenNumbers);
            if (matchCount == 15) {
                if (matched15 > 0) {
                    uint256 prizeAmount = jackpotShare / matched15;
                    winnings[tickets[i].player] += prizeAmount;
                    require(oneToken.transfer(tickets[i].player, prizeAmount), "Token transfer failed.");
                    emit PrizeClaimed(tickets[i].player, prizeAmount);
                }
            } else if (matchCount == 14) {
                if (matched14 > 0) {
                    uint256 prizeAmount = shareMatched14 / matched14;
                    winnings[tickets[i].player] += prizeAmount;
                    require(oneToken.transfer(tickets[i].player, prizeAmount), "Token transfer failed.");
                    emit PrizeClaimed(tickets[i].player, prizeAmount);
                }
            } else if (matchCount == 13) {
                if (matched13 > 0) {
                    uint256 prizeAmount = shareMatched13 / matched13;
                    winnings[tickets[i].player] += prizeAmount;
                    require(oneToken.transfer(tickets[i].player, prizeAmount), "Token transfer failed.");
                    emit PrizeClaimed(tickets[i].player, prizeAmount);
                }
            } else if (matchCount == 12) {
                if (matched12 > 0) {
                    uint256 prizeAmount = shareMatched12 / matched12;
                    winnings[tickets[i].player] += prizeAmount;
                    require(oneToken.transfer(tickets[i].player, prizeAmount), "Token transfer failed.");
                    emit PrizeClaimed(tickets[i].player, prizeAmount);
                }
            } else if (matchCount == 11) {
                if (matched11 > 0) {
                    uint256 prizeAmount = shareMatched11 / matched11;
                    winnings[tickets[i].player] += prizeAmount;
                    require(oneToken.transfer(tickets[i].player, prizeAmount), "Token transfer failed.");
                    emit PrizeClaimed(tickets[i].player, prizeAmount);
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
        require(oneToken.transfer(owner(), _amount), "Token transfer failed.");
    }

    // Additional owner functions to update funds
    function updateProjectFund(uint256 _newAmount) external onlyOwner {
        projectFund = _newAmount;
    }

    function updateGrantFund(uint256 _newAmount) external onlyOwner {
        grantFund = _newAmount;
    }

    function updateOperationFund(uint256 _newAmount) external onlyOwner {
        operationFund = _newAmount;
    }
}
