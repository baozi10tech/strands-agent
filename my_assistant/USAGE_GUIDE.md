# Multi-Agent Customer Service System - Usage Guide

## Overview

This is a multi-agent customer service system that simulates Amazon's customer service negotiation process. It consists of three specialized agents that communicate using the A2A (Agent-to-Agent) protocol.

## System Architecture

```
Customer CLI → Coordinator Agent (Port 9001)
                      ↓
             Negotiation Agent (Port 9002)
                      ↓
                Context Agent (Port 9000)
                      ↓
              CS Simulator CLI (Human)
```

### Agents

1. **Context Agent (Port 9000)**
   - Provides policy information
   - Retrieves order details
   - Recommends negotiation strategies
   - Validates actions against policies

2. **Negotiation Agent (Port 9002)**
   - Conducts negotiations with Customer Service
   - Consults Context Agent via A2A
   - Uses message queue to communicate with CS Simulator
   - Tracks negotiation progress

3. **Coordinator Agent (Port 9001)**
   - Receives customer issues
   - Analyzes issue type
   - Delegates to Negotiation Agent
   - Monitors and reports progress

## Quick Start

### 1. Start the Agent Servers

Open Terminal 1:
```bash
cd my_assistant
python launch_agents.py
```

This will start all three agent servers. Keep this terminal running.

### 2. Start CS Simulator

Open Terminal 2:
```bash
cd my_assistant
python -m cli.cs_simulator_cli
```

You will act as Amazon Customer Service representative. Wait for customer messages and respond appropriately.

### 3. Start Customer CLI

Open Terminal 3:
```bash
cd my_assistant
python -m cli.customer_cli
```

Describe your customer service issue and the system will handle it.

## Example Scenarios

### Scenario 1: Damaged Item

**Customer Input:**
```
My Dell laptop arrived damaged. The screen is cracked. Order 123-4567890-1234567
```

**What Happens:**
1. Coordinator Agent analyzes the issue (damaged_item)
2. Delegates to Negotiation Agent
3. Negotiation Agent consults Context Agent for damaged item policy
4. Negotiation Agent gets strategy recommendations
5. Negotiation Agent sends opening message to CS Simulator
6. Human in CS Simulator responds
7. Negotiation continues until resolved

### Scenario 2: Late Delivery

**Customer Input:**
```
My package is 5 days late. Order 123-7890123-4567890. I need it urgently.
```

**What Happens:**
1. Issue analyzed as late_delivery
2. System retrieves late delivery policy
3. System checks if customer has Prime
4. Negotiation strategy considers compensation options
5. Human CS provides resolution

### Scenario 3: Return Request

**Customer Input:**
```
I want to return an Echo Dot I bought 20 days ago. Order 123-2345678-9012345
```

**What Happens:**
1. Issue analyzed as return_standard
2. System checks 30-day return policy
3. Confirms return eligibility
4. Negotiation proceeds with return authorization

## Available Commands

### Customer CLI Commands
- `/help` - Show usage examples
- `/status` - Check current issue status
- `/quit` - Exit the customer CLI

### CS Simulator CLI Commands
- `/history` - Show conversation history
- `/quit` - Exit the CS simulator

## Testing Individual Agents

Each agent can be tested standalone:

### Test Context Agent
```bash
cd my_assistant
python -m agents.context_agent
```

Try commands like:
- `Get policy P-247`
- `Search for return policies`
- `Get order 123-4567890-1234567`
- `stats` (to see tool usage statistics)

### Test Negotiation Agent
```bash
cd my_assistant
python -m agents.negotiation_agent
```

**Prerequisites:** Context Agent must be running on port 9000

Try commands like:
- `I need to negotiate a damaged item issue`
- `stats` (to see negotiation statistics)

### Test Coordinator Agent
```bash
cd my_assistant
python -m agents.coordinator_agent
```

**Prerequisites:** Negotiation Agent must be running on port 9002

Try commands like:
- `My package arrived damaged`
- `stats` (to see coordination statistics)

## Data Files

The system uses mock data stored in JSON files:

- `data/policies.json` - Amazon policies (5 policies)
- `data/orders.json` - Sample orders (3 orders)
- `data/strategies.json` - Negotiation strategies (5 strategies)

You can modify these files to test different scenarios.

## Session Management

All agents use FileSessionManager to persist conversation history and state:

- Sessions are stored in `my_assistant_sessions/`
- Each agent has its own session subdirectory
- Conversation history is preserved across restarts

To view session data:
```bash
ls -la my_assistant_sessions/
```

## Message Queue

The message queue enables communication between Negotiation Agent and CS Simulator:

- Handles bidirectional async/sync coordination
- Tracks full conversation history
- Global singleton pattern for cross-process sharing

## Troubleshooting

### Agents Not Starting

**Problem:** Agents fail to start with port errors

**Solution:** Make sure ports 9000, 9001, 9002 are not in use:
```bash
lsof -i :9000
lsof -i :9001
lsof -i :9002
```

Kill any processes using these ports.

### A2A Connection Errors

**Problem:** "Error consulting Context Agent" or similar

**Solution:** Ensure agents are started in order:
1. Context Agent (9000) first
2. Negotiation Agent (9002) second  
3. Coordinator Agent (9001) last

Wait 2-3 seconds between each agent startup.

### Message Queue Timeout

**Problem:** "Timeout waiting for CS response"

**Solution:** Make sure CS Simulator CLI is running and human is responding to messages.

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'strands_agents'`

**Solution:** Install requirements:
```bash
pip install -r my_assistant/requirements.txt
```

## Advanced Usage

### Custom Session IDs

You can specify custom session IDs for testing:

```bash
python -m agents.context_agent --session-id my-test-session
```

### Custom Storage Directory

```bash
python -m agents.context_agent --storage-dir ./custom_sessions
```

### Viewing Agent State

All agents track tool usage and state. Use the `stats` command in any standalone agent to view:

**Context Agent Stats:**
- tool_get_policy_count
- tool_search_policies_count
- tool_get_order_count
- etc.

**Negotiation Agent Stats:**
- tool_consult_context_agent_count
- messages_sent_to_cs
- responses_received_from_cs
- negotiation_outcome

**Coordinator Agent Stats:**
- tool_analyze_customer_issue_count
- tool_delegate_to_negotiation_agent_count
- case_resolution

## System Requirements

- Python 3.8+
- strands-agents SDK
- asyncio support
- 3 available ports (9000, 9001, 9002)

## Next Steps

1. Try the example scenarios above
2. Modify the data files to create custom policies
3. Observe how agents communicate via A2A
4. Experiment with different negotiation strategies
5. Review session files to see conversation persistence

## Additional Resources

- Strands Agents Documentation: https://strandsagents.com
- A2A Protocol Guide: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-to-agent/
- Demo Folder: `demo/` - See working examples of each concept

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the demo folder for working examples
3. Examine the code documentation in each agent file
