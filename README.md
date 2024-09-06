# CryptoDraw

CryptoDraw is a decentralized, blockchain-powered lottery game that offers participants a fair, transparent, and exciting way to win substantial rewards. Built on Ethereum-compatible networks, CryptoDraw uses smart contracts and Chainlink's Verifiable Random Function (VRF) to ensure the integrity of each draw.

## Game Overview

CryptoDraw is a strategic lottery game where players select a set of numbers in hopes of matching them with the randomly drawn winning numbers. The game is designed to reward both jackpot winners and those who come close, with multiple prize tiers ensuring that even near misses are recognized.

### How to Play

1. **Select Your Numbers**: Choose between 15 and 20 numbers from a pool of 25 possible numbers.
2. **Purchase a Ticket**: The ticket price is dynamically calculated based on the number of chosen numbers. The base price is (tbd) token per ticket.
3. **Wait for the Draw**: Draws occur every 4 days, and the winning numbers are generated using Chainlink VRF.
4. **Match to Win**: Your ticket is evaluated based on how many of your chosen numbers match the winning numbers.
5. **Claim Your Prize**: If your numbers match enough of the winning numbers, you can claim your prize directly from the smart contract.

### Strategic Considerations

- **Number Selection**: Selecting more numbers increases your chances of winning but also increases the ticket cost. Choose wisely to balance cost and potential rewards.
- **Timing**: With draws occurring every 4 days, timing your ticket purchase can be crucial, especially as the prize pool grows.
- **Agent Sales**: Agents who sell tickets receive commissions, with additional bonuses for electronic sales, incentivizing widespread ticket distribution.

## Prize Breakdown

CryptoDraw offers a tiered prize structure, ensuring rewards across multiple levels of matching numbers. The prize pool is distributed as follows:

### Arrecadation split
**Numerical Prognostics** | **Percentage**
--- | ---
Gross Prize | 43.35%
Lottery Agents' Commission* | 8.61%
Lottery Development Fund (FDL) | 1.95%
Operational Expense Costs | 9.57%
Chain Health Investment Program | 24.96%
Grant Fund | 7.72%
Operation Fund (accumulate to final 0 draw) | 4.93%
**Total** | **100%**

### Prize Tiers

- **Jackpot (15 Matches)**: 75% of the total Gross prize pool is allocated to jackpot winners.
- **14 Matches**: 14% of the prize pool.
- **13 Matches**: 5% of the prize pool.
- **12 Matches**: 3% of the prize pool.
- **11 Matches**: 2% of the prize pool.

### Chances of win (1 in:)* 
**Probability**

| Prize Tiers | Simple Bets | | | | | |
| --- | --- | --- | --- | --- | --- | --- |
|  | 15 Numbers (1 bet) | 16 Numbers (16 bets) | 17 Numbers (136 bets) | 18 Numbers (816 bets) | 19 Numbers (3,876 bets) | 20 Numbers (15,504 bets) |
| **15 Matches** | 3,268,760 | 204,298 | 24,035 | 4,006 | 843 | 211 |
| **14 Matches** | 21,792 | 3,027 | 601 | 153 | 47 | 17 |
| **13 Matches** | 692 | 162 | 49 | 18 | 8 | 4.2 |
| **12 Matches** | 60 | 21 | 9 | 5 | 3.2 | 2.6 |
| **11 Matches** | 11 | 6 | 4 | 3 | 2.9 | 3.9 |
| **PRICE TO PAY** | 1 x $3.00 = $3.00 | 16 x $3.00 = $48.00 | 136 x $3.00 = $408.00 | 816 x $3.00 = $2,448.00 | 3,876 x $3.00 = $11,628.00 | 15,504 x $3.00 = $46,512.00 |

*note: Example considering ticket at price $3 usd worth

### Additional Fund Allocations

- **Agent Commissions**: 8.61% of the total prize pool goes to agents.
- **Chain Health Investment**: 24.96% of the prize pool is reserved for long-term sustainability and growth of the blockchain network.
- **Operational Expenses**: 9.57% is allocated to covering operational costs.
- **Grant Fund**: 7.72% is set aside for future project grants.
- **Lottery Development Fund (FDL)**: 0.95% is allocated to ongoing development and improvements.

### Prize Distribution Example

For example, if the total prize pool is 1,000,000 tokens:

- **Jackpot Winners (15 Matches)**: 750,000 tokens are shared among those who match all 15 numbers.
- **14 Matches**: 140,000 tokens are shared among those who match 14 numbers.
- **13 Matches**: 50,000 tokens are shared among those who match 13 numbers.
- **12 Matches**: 30,000 tokens are shared among those who match 12 numbers.
- **11 Matches**: 20,000 tokens are shared among those who match 11 numbers.

## Key Features

- **Chainlink VRF**: Ensures that the number selection is provably fair and cannot be tampered with.
- **Decentralized**: All transactions and processes are conducted on-chain, providing transparency and security.
- **Dynamic Ticket Pricing**: The cost of participation scales with the number of selected numbers, offering strategic depth.

## Technical Overview

CryptoDraw is implemented in Solidity and deployed on Ethereum-compatible networks. Key technologies include:

- **Solidity**: For smart contract development.
- **Chainlink VRF**: For verifiable random number generation.
- **OpenZeppelin Contracts**: Providing secure token and access control implementations.
- **Hardhat**: For local development, testing, and deployment of the smart contracts.

## Deployment

CryptoDraw can be deployed on various EVM-compatible networks, including:

- Ethereum Mainnet
- Sepolia
- Harmony
- Binance Smart Chain (BSC)
- opBNB

## Contributing

We welcome contributions to the CryptoDraw project. Please submit issues or pull requests to suggest improvements or report bugs.

## License

CryptoDraw is open-source and available under the MIT License.
