# Agents Overview

**Agent Compensation in CryptoDraw**

Agents in the CryptoDraw game are compensated through a commission-based model, which incentivizes them to promote the game and sell tickets to players. Here's a detailed breakdown of how agents are paid:

1. **Commission on Ticket Sales:**
   Agents earn a commission for every ticket they sell to players. The commission rate is set at **8.61%** of the total ticket price. This rate is fixed in the smart contract and is automatically calculated and credited to the agent's account when a player purchases a ticket through them. 

2. **Automatic Calculation and Distribution:**
   When a player buys a ticket, the smart contract performs the following actions:
   - The total ticket cost in the native ERC-20 token is calculated, taking into account the number of chosen numbers and the ticket's base price in USD.
   - The agent's commission is calculated as **8.61%** of the ticket cost.
   - The calculated commission amount is credited to the agent's account (tracked in the `agentCommissions` mapping), and the total ticket sales by the agent are updated for the corresponding draw round (`agentTicketsSold` mapping).

3. **Payout of Agent Commissions:**
   The commissions accumulated in the `agentCommissions` mapping are distributed at the end of each draw round. The distribution process is as follows:
   - After the draw round ends and the winning numbers are determined, the contract checks the total commissions owed to each agent.
   - The smart contract then initiates a secure transfer of the accumulated commission amount from the contract’s balance to the agent’s wallet. This process is automated and happens without any manual intervention, ensuring timely and accurate payments.

4. **Agent Status and Eligibility:**
   Agents must maintain an active status in the game to be eligible for commissions. The `agentStatus` mapping tracks whether an agent is active or inactive. Only agents with an active status are allowed to sell tickets and earn commissions. The game administrators can manage agent status through the `setAgentStatus` function.

5. **Transparency and Auditability:**
   All agent transactions, including ticket sales and commission payments, are recorded on the blockchain, ensuring full transparency and auditability. Agents can check their total tickets sold, commissions earned, and any payments made directly from the smart contract by querying the relevant functions (`getAgentCommission` and `agentTicketsSold`).

6. **Role of Chainlink Automation:**
   The distribution of agent commissions is also supported by Chainlink Automation (Keepers). This ensures that payouts occur automatically at predefined intervals (e.g., after each draw), reducing the need for manual checks and mitigating delays.

By using smart contracts and decentralized oracles, CryptoDraw guarantees that agent payments are handled securely, transparently, and efficiently, promoting trust and encouraging agent participation in the ecosystem.

### Claiming Commission

In the CryptoDraw game, agents can claim their commissions automatically once they are earned from the sale of tickets. The commission is tracked in the agentCommissions mapping, which keeps a record of the total amount owed to each agent.

Here's how the claiming process works:

Automatic Commission Crediting: When a player purchases a ticket through an agent, the contract calculates the agent's commission (8.61% of the ticket price) and adds it to the agent's total in the agentCommissions mapping.

Distribution of Commissions: During the prize distribution process, the contract checks the agentCommissions for each agent. If an agent has earned commissions, the contract transfers the amount owed from the contract balance to the agent's address.

Resetting After Payment: Once the commission is paid, the amount in agentCommissions for that agent is reset to zero. This ensures that each commission is only paid once per round.

Events for Transparency: The contract emits the AgentCommissionPaid event when commissions are paid, providing transparency and allowing agents to track their earnings.

Agents do not need to manually claim their commissions; the smart contract handles the entire process during prize distribution after each draw. This automated system ensures a smooth and transparent payout mechanism for all agents involved in the CryptoDraw project.