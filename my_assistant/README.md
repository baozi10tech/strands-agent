# Strands Agent - Multi-Agent Customer Service Assistant

A prototype multi-agent application that assists customers by communicating with Amazon Customer Service on their behalf to resolve issues.

## System Overview

**Strands Agent** is a customer-side intelligent assistant that uses a three-agent distributed architecture to handle customer service interactions. The system takes customer issues, gathers necessary context, and autonomously negotiates with Amazon Customer Service via chat to resolve problems.

### Key Features

- **Customer-Side Application**: Acts on behalf of the customer, not Amazon
- **Multi-Agent Architecture**: Three specialized agents working together via A2A protocol
- **Autonomous Negotiation**: Handles Amazon CS conversations without customer intervention
- **Policy-Aware**: Understands Amazon policies, tools, and strategies
- **Dual CLI Interface**: Separate interfaces for customer interaction and CS monitoring

## Architecture

### Three-Agent A2A System

All three agents are implemented as A2A (Agent-to-Agent) servers, enabling true distributed multi-agent communication:

```
┌─────────────────────────────────────────────────────────────────┐
│                     STRANDS AGENT SYSTEM                        │
│                    (Customer-Side Application)                  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  Context Agent   │◄────────┤ Coordinator Agent│────────►│ Negotiation Agent│
│   (Port 9000)    │   A2A   │   (Port 9001)    │   A2A   │   (Port 9002)    │
│                  │         │                  │         │                  │
│ • Policy KB      │         │ • Customer CLI   │         │ • CS Chat CLI    │
│ • Order Data     │         │ • Orchestration  │         │ • Strategy Exec  │
│ • Strategy KB    │         │ • Clarification  │         │ • Issue Resolution│
│ • LLM Reasoning  │         │ • Goal Setting   │         │ • Progress Track │
└──────────────────┘         └──────────────────┘         └──────────────────┘
         ▲                            ▲                            │
         │                            │                            │
         │                            │                            ▼
         │                    ┌───────────────┐          ┌─────────────────┐
         │                    │  Customer     │          │  Mock Amazon CS │
         │                    │  (CLI #1)     │          │  Bot (CLI #2)   │
         │                    └───────────────┘          └─────────────────┘
         │                                                         ▲
         └─────────────────────────────────────────────────────────┘
                    (All agents can query Context Agent)
```

### Agent Descriptions

#### 1. Context Agent (Port 9000)

**Role**: Intelligent knowledge base with reasoning capabilities

**Capabilities**:
- Policy lookup and interpretation
- Order data retrieval and analysis
- Negotiation strategy recommendations
- Tool availability checking
- LLM-powered reasoning for complex queries
- Guardrails and validation

**Tools Exposed**:
- `get_policy(policy_name)` - Retrieve specific policy details
- `search_policies(query)` - Semantic search across policies
- `get_order(order_id)` - Retrieve order information
- `get_customer_history()` - Get customer's order history
- `recommend_strategy(issue_type)` - Get negotiation strategies
- `validate_action(action_type, params)` - Validate proposed actions

**Why A2A Server?**
- Enables intelligent reasoning, not just lookups
- Can provide context-aware recommendations
- Supports future RAG and vector search integration
- Allows for learning and adaptation over time

#### 2. Coordinator Agent (Port 9001)

**Role**: Customer interface and system orchestrator

**Capabilities**:
- Customer interaction via CLI
- Issue understanding and clarification
- Goal setting for negotiation
- Progress monitoring
- Multi-turn conversation management
- Result presentation to customer

**A2A Communication**:
- **To Context Agent**: Query policies, orders, strategies
- **To Negotiation Agent**: Initiate resolution, get updates, retrieve results

**CLI Interface #1**: Customer Chat
```
Customer: I need to return my damaged laptop
Coordinator: Let me help you with that. Can you provide your order ID?
Customer: 123-4567890-1234567
Coordinator: [Queries Context Agent for order details]
Coordinator: I see your order. I'll negotiate with Amazon CS now.
Coordinator: [Initiates Negotiation Agent with goal]
Coordinator: [Updates customer on progress]
Coordinator: Great news! I've arranged a full refund and return label...
```

#### 3. Negotiation Agent (Port 9002)

**Role**: Amazon Customer Service interface and negotiation executor

**Capabilities**:
- Chat with Mock Amazon CS bot
- Execute negotiation strategies
- Track conversation state
- Adapt tactics based on CS responses
- Report progress back to Coordinator

**A2A Communication**:
- **To Context Agent**: Get strategies, validate actions, check policies
- **From Coordinator**: Receive goals, send updates, return results

**CLI Interface #2**: CS Chat Monitor (Optional for customer visibility)
```
[Negotiation Agent -> Amazon CS Bot]
NA: Hello, I need help with order 123-4567890-1234567
CS: Hello! How can I assist you today?
NA: The laptop arrived damaged. I'd like a refund and return label.
CS: I see. Can you describe the damage?
NA: [Queries Context Agent for policy on damaged items]
NA: The screen is cracked and won't turn on. Per policy P-247...
CS: Let me process that refund for you right away...
```

## A2A Communication Flow

### Example: Damaged Item Return

```
1. Customer Input (CLI #1)
   Customer -> Coordinator: "My laptop arrived damaged, I want a refund"

2. Issue Understanding
   Coordinator -> Context Agent (A2A): get_order("123-4567890-1234567")
   Context Agent -> Coordinator: {order_details}
   
   Coordinator -> Context Agent (A2A): search_policies("damaged item return")
   Context Agent -> Coordinator: {relevant_policies}

3. Goal Setting
   Coordinator creates negotiation goal:
   {
     "goal": "obtain_full_refund_and_return_label",
     "order_id": "123-4567890-1234567",
     "issue_type": "damaged_item",
     "customer_sentiment": "frustrated"
   }

4. Negotiation Initiation
   Coordinator -> Negotiation Agent (A2A): initiate_resolution(goal)
   
5. Negotiation Execution
   Negotiation Agent -> Context Agent (A2A): recommend_strategy("damaged_item")
   Context Agent -> Negotiation Agent: {strategy: "cite_policy_P247", escalation_path: [...]}
   
   Negotiation Agent -> Mock CS Bot: [Chat conversation]
   
   Negotiation Agent -> Context Agent (A2A): validate_action("accept_refund", {amount: 999.99})
   Context Agent -> Negotiation Agent: {valid: true, within_policy: true}

6. Progress Updates
   Negotiation Agent -> Coordinator (A2A): update_status("refund_approved")
   Coordinator -> Customer: "Great news! Refund of $999.99 approved..."

7. Resolution
   Negotiation Agent -> Coordinator (A2A): resolution_complete({
     "outcome": "success",
     "refund_amount": 999.99,
     "return_label": "LABEL-123",
     "conversation_log": [...]
   })
   
   Coordinator -> Customer: [Present final resolution]
```

## Technology Stack

### Core Framework
- **Strands Agents SDK** (v1.0.0+): Multi-agent orchestration
- **A2A Protocol**: Standardized agent-to-agent communication
- **Python 3.8+**: Primary language
- **asyncio**: Async/concurrent operations

### Key Dependencies
```
strands-agents>=1.0.0
strands-agents-tools>=0.2.0
```

### Agent Implementation
```python
from strands import Agent, tool
from strands.multiagent.a2a import A2AServer, A2AClient

# Each agent runs as an A2A server
server = A2AServer(agent=my_agent, port=9000)
await server.start()

# Agents communicate via A2A clients
client = A2AClient(url="http://localhost:9000")
response = await client.call_tool("get_policy", {"policy_name": "P-247"})
```

## Mock Data Components

### 1. Policies (policies.json)
```json
{
  "P-247": {
    "name": "Damaged Item Return Policy",
    "description": "Full refund for items damaged in shipping",
    "conditions": ["Item damaged", "Reported within 30 days"],
    "actions": ["Full refund", "Return label provided", "No restocking fee"]
  },
  "P-189": {
    "name": "Late Delivery Compensation",
    "description": "Credit for deliveries past guaranteed date",
    "conditions": ["Prime member", "Guaranteed delivery missed"],
    "actions": ["$10 credit", "Refund shipping"]
  }
}
```

### 2. Orders (orders.json)
```json
{
  "123-4567890-1234567": {
    "order_id": "123-4567890-1234567",
    "customer_id": "C-12345",
    "items": [
      {
        "asin": "B08N5WRWNW",
        "name": "Dell XPS 13 Laptop",
        "price": 999.99,
        "quantity": 1
      }
    ],
    "order_date": "2024-01-15",
    "delivery_date": "2024-01-20",
    "status": "delivered"
  }
}
```

### 3. Strategies (strategies.json)
```json
{
  "damaged_item": {
    "initial_approach": "polite_direct",
    "key_points": [
      "Reference specific policy number",
      "Provide evidence of damage",
      "Request immediate resolution"
    ],
    "escalation_triggers": [
      "CS refuses refund",
      "Offered partial refund only",
      "Requests return without label"
    ],
    "escalation_tactics": [
      "Request supervisor",
      "Cite policy explicitly",
      "Mention Prime membership"
    ]
  }
}
```

## Project Structure

```
strands-agent/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
│
├── agents/
│   ├── __init__.py
│   ├── context_agent.py              # Context Agent (Port 9000)
│   ├── coordinator_agent.py          # Coordinator Agent (Port 9001)
│   └── negotiation_agent.py          # Negotiation Agent (Port 9002)
│
├── data/
│   ├── policies.json                 # Mock Amazon policies
│   ├── orders.json                   # Mock order data
│   └── strategies.json               # Negotiation strategies
│
├── cli/
│   ├── __init__.py
│   ├── customer_cli.py               # CLI #1: Customer interface
│   └── cs_monitor_cli.py             # CLI #2: CS chat monitor
│
├── mock/
│   ├── __init__.py
│   └── amazon_cs_bot.py              # Mock Amazon CS bot
│
├── utils/
│   ├── __init__.py
│   ├── a2a_client.py                 # A2A client helper
│   └── logger.py                     # Logging utilities
│
└── main.py                           # Launch all agents
```

## Running the System

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start All Agents
```bash
python main.py
```

This will start:
- Context Agent on port 9000
- Coordinator Agent on port 9001
- Negotiation Agent on port 9002

### 3. Launch Customer CLI
```bash
python cli/customer_cli.py
```

### 4. (Optional) Monitor CS Conversation
```bash
python cli/cs_monitor_cli.py
```

## Benefits of Full A2A Architecture

### 1. **True Multi-Agent System**
- Each agent operates independently with its own reasoning
- Distributed architecture allows for scaling and resilience
- No single point of failure

### 2. **Intelligent Context Agent**
- Not just a lookup service - can reason about policies
- Provides guardrails and validation
- Can learn and adapt over time
- Ready for RAG and vector search integration

### 3. **Clean Separation of Concerns**
- Context: Knowledge and reasoning
- Coordinator: Customer interaction and orchestration
- Negotiation: CS communication and strategy execution

### 4. **Extensibility**
- Easy to add new agents (e.g., Analytics Agent, Escalation Agent)
- Tools can be added without changing agent architecture
- A2A protocol is an open standard

### 5. **Realistic Prototype**
- Models how production system would work
- A2A communication patterns are production-ready
- Can easily transition to real integrations

## Future Enhancements

- **Real Amazon Integration**: Replace mock CS bot with actual Amazon API
- **Vector Search**: Add semantic search for policies and past resolutions
- **Learning System**: Train negotiation strategies from successful resolutions
- **Multi-Customer Support**: Handle multiple customers concurrently
- **Analytics Dashboard**: Track resolution success rates and patterns
- **Voice Interface**: Add voice support for customer interactions

## Development Notes

This is a prototype with simulated components:
- Amazon CS bot is mocked for testing
- Policies and orders are fake data
- CLI interfaces simulate real-time chat
- A2A communication uses local network only

The architecture is designed to be production-ready, allowing easy transition from mock to real integrations.

---

**Built with Strands Agents SDK** - Agent-to-Agent Communication Protocol
