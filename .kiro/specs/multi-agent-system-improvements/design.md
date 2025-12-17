# Design Document: Multi-Agent Customer Service System Improvements

## Overview

This design document outlines improvements to the existing multi-agent customer service negotiation system. The system currently consists of three agents (Context, Negotiation, and Coordinator) that communicate via the A2A protocol to handle customer service issues autonomously.

The improvements focus on:
1. **Enhanced A2A Communication** - Implementing streaming responses and proper client patterns
2. **Real-Time Monitoring** - Adding observability and metrics collection
3. **Intelligent Negotiation** - Adaptive strategies based on conversation context
4. **Scalability** - Supporting multiple concurrent conversations
5. **Robustness** - Improved error handling, persistence, and recovery

### Current Architecture

```
Customer CLI → Coordinator Agent (Port 9001)
                      ↓ A2A
             Negotiation Agent (Port 9002)
                      ↓ A2A
                Context Agent (Port 9000)
                      ↓ Message Queue
              CS Simulator CLI (Human)
```

### Improved Architecture

```
                    ┌─────────────────────┐
                    │  Load Balancer      │
                    │  (Path-based mount) │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐    ┌───────▼────────┐    ┌───────▼────────┐
│ Coordinator    │    │ Negotiation    │    │ Context        │
│ Agent (9001)   │◄──►│ Agent (9002)   │◄──►│ Agent (9000)   │
│                │ A2A│                │ A2A│                │
│ - TaskStore    │    │ - TaskStore    │    │ - TaskStore    │
│ - QueueMgr     │    │ - QueueMgr     │    │ - Analytics    │
└────────┬───────┘    └────────┬───────┘    └────────┬───────┘
         │                     │                      │
         │                     │                      │
    ┌────▼─────────────────────▼──────────────────────▼────┐
    │         Monitoring & Analytics Dashboard              │
    │  - Agent Status  - Metrics  - Conversation Logs      │
    └───────────────────────────────────────────────────────┘
```

## Architecture

### Component Overview

#### 1. Enhanced A2A Communication Layer

**Purpose**: Provide robust, streaming-capable agent-to-agent communication

**Key Components**:
- `A2AClientManager`: Manages client instances with connection pooling
- `StreamingMessageHandler`: Processes streaming responses incrementally
- `AgentCardCache`: Caches discovered agent cards to avoid repeated discovery
- `A2AErrorHandler`: Implements retry logic and error recovery

**Communication Patterns**:
1. **Synchronous Request-Response**: For simple queries (policy lookup, order retrieval)
2. **Streaming Responses**: For long-running operations (negotiation execution, complex reasoning)
3. **Agent-as-Tool**: Wrapped A2A agents for composition into workflows

#### 2. Monitoring and Observability System

**Purpose**: Provide real-time visibility into agent activities and system health

**Key Components**:
- `MetricsCollector`: Collects and aggregates metrics from all agents
- `EventLogger`: Structured logging with correlation IDs
- `MonitoringDashboard`: Web-based real-time dashboard
- `AlertManager`: Threshold-based alerting for anomalies

**Metrics Tracked**:
- A2A message latency (p50, p95, p99)
- Tool invocation counts and success rates
- Conversation duration and outcome
- Agent CPU/memory utilization
- Message queue depth

#### 3. Intelligent Negotiation Engine

**Purpose**: Adapt negotiation tactics based on conversation context and CS responses

**Key Components**:
- `SentimentAnalyzer`: Analyzes CS response sentiment
- `StrategySelector`: Chooses optimal strategy based on context
- `EscalationManager`: Determines when and how to escalate
- `OutcomePredictor`: Predicts negotiation success probability

**Strategy Selection Algorithm**:
```python
def select_strategy(issue_type, conversation_history, cs_sentiment):
    # 1. Get base strategy for issue type
    base_strategy = strategies[issue_type]
    
    # 2. Analyze conversation progress
    progress = analyze_progress(conversation_history)
    
    # 3. Check escalation triggers
    if should_escalate(progress, cs_sentiment):
        return base_strategy.escalation_tactics
    
    # 4. Adapt based on sentiment
    return adapt_strategy(base_strategy, cs_sentiment)
```

#### 4. Context Agent Enhancements

**Purpose**: Provide intelligent, context-aware policy recommendations

**Key Components**:
- `PolicyRanker`: Ranks policies by relevance with confidence scores
- `MultiSourceReasoner`: Synthesizes information from multiple data sources
- `ValidationEngine`: Validates actions against all applicable policies
- `HistoryAnalyzer`: Considers customer history in recommendations

**Policy Recommendation Flow**:
```
Query → Extract Context → Search Policies → Rank by Relevance → 
Validate Conditions → Generate Recommendations with Confidence Scores
```

#### 5. Conversation State Management

**Purpose**: Robust state persistence and recovery for all conversations

**Key Components**:
- `ConversationStateStore`: Persistent storage for conversation state
- `StateRecoveryManager`: Recovers state after failures
- `TransactionLog`: Write-ahead log for state changes
- `StateValidator`: Validates state integrity

**State Schema**:
```python
ConversationState = {
    "conversation_id": str,
    "customer_id": str,
    "issue_type": str,
    "current_phase": str,  # analysis, negotiation, resolution
    "message_history": List[Message],
    "agent_state": Dict[str, Any],
    "metadata": {
        "created_at": datetime,
        "updated_at": datetime,
        "status": str
    }
}
```

#### 6. Multi-Customer Support System

**Purpose**: Handle multiple concurrent conversations with isolation

**Key Components**:
- `CustomTaskStore`: Implements A2A TaskStore interface for conversation isolation
- `CustomQueueManager`: Implements A2A QueueManager for request prioritization
- `ConversationRouter`: Routes requests to appropriate agent instances
- `ResourceManager`: Manages agent instance lifecycle

**Task Store Implementation**:
```python
class ConversationTaskStore(TaskStore):
    """Custom TaskStore that isolates conversations by customer_id"""
    
    async def create_task(self, task: Task) -> Task:
        # Store task with customer_id isolation
        pass
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        # Retrieve task with proper isolation
        pass
    
    async def update_task(self, task: Task) -> Task:
        # Update task state atomically
        pass
```

## Components and Interfaces

### A2A Client Manager

**Interface**:
```python
class A2AClientManager:
    """Manages A2A client connections with caching and pooling"""
    
    async def get_client(
        self, 
        agent_url: str, 
        streaming: bool = False
    ) -> A2AClient:
        """Get or create A2A client for agent"""
        pass
    
    async def discover_agent(self, agent_url: str) -> AgentCard:
        """Discover agent capabilities (cached)"""
        pass
    
    async def send_message(
        self,
        agent_url: str,
        message: str,
        streaming: bool = False
    ) -> AsyncIterator[Union[Message, Tuple[Task, UpdateEvent]]]:
        """Send message to agent with streaming support"""
        pass
```

**Usage Example**:
```python
# Initialize manager
client_mgr = A2AClientManager()

# Send streaming message
async for event in client_mgr.send_message(
    agent_url="http://localhost:9000",
    message="What's the damaged item policy?",
    streaming=True
):
    if isinstance(event, Message):
        process_message(event)
    elif isinstance(event, tuple):
        task, update = event
        process_update(task, update)
```

### Monitoring Dashboard API

**Interface**:
```python
class MonitoringAPI:
    """REST API for monitoring dashboard"""
    
    async def get_agent_status(self) -> List[AgentStatus]:
        """Get status of all agents"""
        pass
    
    async def get_metrics(
        self, 
        time_range: TimeRange,
        metric_names: List[str]
    ) -> MetricsData:
        """Get metrics for specified time range"""
        pass
    
    async def get_active_conversations(self) -> List[ConversationSummary]:
        """Get all active conversations"""
        pass
    
    async def get_conversation_details(
        self, 
        conversation_id: str
    ) -> ConversationDetails:
        """Get detailed conversation information"""
        pass
```

### Strategy Selector

**Interface**:
```python
class StrategySelector:
    """Selects optimal negotiation strategy"""
    
    def select_strategy(
        self,
        issue_type: str,
        conversation_history: List[Message],
        cs_sentiment: SentimentScore,
        customer_context: CustomerContext
    ) -> NegotiationStrategy:
        """Select best strategy for current situation"""
        pass
    
    def should_escalate(
        self,
        conversation_history: List[Message],
        current_strategy: NegotiationStrategy
    ) -> bool:
        """Determine if escalation is needed"""
        pass
    
    def get_escalation_tactics(
        self,
        current_strategy: NegotiationStrategy,
        escalation_reason: str
    ) -> List[Tactic]:
        """Get escalation tactics"""
        pass
```

### Agent-as-Tool Wrapper

**Interface**:
```python
class A2AAgentTool:
    """Wraps an A2A agent as a reusable tool"""
    
    def __init__(self, agent_url: str, agent_name: str):
        """Initialize with agent URL and name"""
        self.agent_url = agent_url
        self.agent_name = agent_name
        self.agent_card = None  # Cached
        self.client = None  # Cached
    
    async def initialize(self):
        """Discover agent card and create client (called once)"""
        pass
    
    @tool
    async def call_agent(self, message: str) -> str:
        """Send message to agent and return response"""
        pass
    
    async def refresh_card(self):
        """Refresh cached agent card"""
        pass
```

## Data Models

### Message Models

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class Message:
    """Represents a message in a conversation"""
    message_id: str
    conversation_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ConversationMessage:
    """Extended message with conversation context"""
    message: Message
    sender_agent: str
    receiver_agent: Optional[str]
    latency_ms: float
    success: bool
    error: Optional[str]
```

### Negotiation Models

```python
@dataclass
class NegotiationStrategy:
    """Represents a negotiation strategy"""
    issue_type: str
    initial_approach: str
    key_points: List[str]
    opening_statement: str
    escalation_triggers: List[str]
    escalation_tactics: List[str]
    success_indicators: List[str]

@dataclass
class SentimentScore:
    """Sentiment analysis result"""
    polarity: float  # -1.0 to 1.0
    subjectivity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    emotion: str  # angry, frustrated, neutral, satisfied, happy

@dataclass
class NegotiationOutcome:
    """Result of a negotiation"""
    conversation_id: str
    outcome: str  # success, partial_success, failure
    resolution: str
    customer_satisfaction: str
    duration_seconds: float
    message_count: int
    escalation_count: int
    policies_cited: List[str]
```

### Monitoring Models

```python
@dataclass
class AgentStatus:
    """Status of an agent"""
    agent_id: str
    agent_name: str
    port: int
    status: str  # running, stopped, error
    uptime_seconds: float
    active_conversations: int
    total_messages: int
    error_count: int

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    metric_name: str
    value: float
    labels: Dict[str, str]

@dataclass
class ConversationSummary:
    """Summary of a conversation"""
    conversation_id: str
    customer_id: str
    issue_type: str
    status: str  # active, completed, failed
    started_at: datetime
    duration_seconds: Optional[float]
    message_count: int
    current_agent: str
```

### Configuration Models

```python
@dataclass
class AgentConfig:
    """Configuration for an agent"""
    agent_id: str
    agent_name: str
    port: int
    host: str
    http_url: Optional[str]
    serve_at_root: bool
    timeout_seconds: int
    max_concurrent_conversations: int

@dataclass
class A2AConfig:
    """A2A communication configuration"""
    default_timeout: int
    streaming_enabled: bool
    retry_max_attempts: int
    retry_backoff_factor: float
    connection_pool_size: int
    agent_card_cache_ttl: int

@dataclass
class SystemConfig:
    """Overall system configuration"""
    agents: List[AgentConfig]
    a2a: A2AConfig
    monitoring: MonitoringConfig
    storage: StorageConfig
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated:
- Properties 1.1, 1.2, 1.4, and 1.5 all relate to A2A communication patterns and can be verified through comprehensive A2A communication tests
- Properties 2.1, 2.4 relate to logging/error capture and can be combined into comprehensive logging properties
- Properties 3.1, 3.5 and 11.1 all relate to data recording and can be verified through outcome recording tests
- Properties 5.1 and 5.4 both relate to persistence after events and can be combined
- Properties 7.1 and 7.4 are both round-trip persistence properties

### Communication Properties

Property 1: Streaming client factory usage
*For any* A2A message sent by an agent, the system should use ClientFactory with streaming=True to enable streaming responses
**Validates: Requirements 1.1**

Property 2: Agent discovery before communication
*For any* pair of agents attempting to communicate, the system should use A2ACardResolver to discover agent capabilities before sending the first message
**Validates: Requirements 1.2**

Property 3: Client instance reuse
*For any* set of concurrent A2A communications, the system should reuse httpx.AsyncClient instances rather than creating new instances for each communication
**Validates: Requirements 1.4**

Property 4: Incremental streaming processing
*For any* streaming A2A response containing Message, Task, and UpdateEvent types, the system should process each event type incrementally as it arrives
**Validates: Requirements 1.5**

### Monitoring and Observability Properties

Property 5: Structured logging completeness
*For any* agent action, the system should emit structured log events containing agent ID, action type, and timestamp
**Validates: Requirements 2.1**

Property 6: Error logging completeness
*For any* A2A communication failure, the system should log detailed error information including agent names, timestamps, and failure reasons
**Validates: Requirements 1.3**

Property 7: Error context capture
*For any* agent error, the system should capture full error context including stack traces and agent state
**Validates: Requirements 2.4**

Property 8: Metrics tracking
*For any* A2A communication, the system should track and record message latency and success rate metrics
**Validates: Requirements 2.2**

Property 9: Dashboard information completeness
*For any* monitoring dashboard render, the displayed information should include real-time agent status, active conversations, and performance metrics
**Validates: Requirements 2.3**

Property 10: Metrics query completeness
*For any* system metrics query, the response should provide aggregated statistics for tool usage, conversation outcomes, and resolution times
**Validates: Requirements 2.5**

### Negotiation Intelligence Properties

Property 11: CS response analysis
*For any* CS response received, the system should analyze sentiment and extract key information
**Validates: Requirements 3.1**

Property 12: Escalation trigger evaluation
*For any* negotiation progress evaluation, the system should determine if escalation tactics are needed based on predefined triggers
**Validates: Requirements 3.2**

Property 13: Strategy selection appropriateness
*For any* negotiation scenario with multiple available strategies, the system should select the most appropriate strategy based on issue type and conversation history
**Validates: Requirements 3.3**

Property 14: Automatic impasse escalation
*For any* negotiation that reaches an impasse, the system should automatically escalate using predefined escalation tactics
**Validates: Requirements 3.4**

Property 15: Outcome metrics recording
*For any* completed negotiation, the system should record outcome metrics including success rate, resolution time, and customer satisfaction
**Validates: Requirements 3.5, 11.1**

### Context Agent Properties

Property 16: Multi-factor policy response
*For any* policy query, the system should consider customer history, order details, and issue type in generating the response
**Validates: Requirements 4.1**

Property 17: Policy ranking with reasoning
*For any* scenario where multiple policies apply, the system should rank policies by relevance and provide reasoning for the ranking
**Validates: Requirements 4.2**

Property 18: Comprehensive policy validation
*For any* policy validation request, the system should check all applicable conditions and provide detailed validation results
**Validates: Requirements 4.3**

Property 19: Multi-source LLM synthesis
*For any* complex query, the system should use LLM reasoning to synthesize information from multiple data sources
**Validates: Requirements 4.4**

Property 20: Recommendation completeness
*For any* policy recommendation, the response should include confidence scores and supporting evidence
**Validates: Requirements 4.5**

### State Management Properties

Property 21: Message exchange persistence
*For any* conversation in progress, the system should persist conversation state after each message exchange
**Validates: Requirements 5.1**

Property 22: State restoration round-trip
*For any* conversation state that is persisted, restoring it after an agent restart should produce an equivalent state
**Validates: Requirements 5.2**

Property 23: Thread-safe state access
*For any* set of concurrent operations accessing conversation state, the system should provide thread-safe access without race conditions or data corruption
**Validates: Requirements 5.3**

Property 24: Conversation archival completeness
*For any* completed conversation, the system should archive the full conversation history with metadata
**Validates: Requirements 5.4**

Property 25: Corruption detection and recovery
*For any* corrupted conversation state, the system should detect the corruption and initiate recovery procedures
**Validates: Requirements 5.5**

### Multi-Customer Concurrency Properties

Property 26: Task isolation
*For any* set of concurrent customer issue submissions, the system should create isolated Task instances for each customer conversation
**Validates: Requirements 6.1**

Property 27: TaskStore state separation
*For any* agent processing multiple conversations, the system should use custom TaskStore implementations to maintain separate state for each conversation
**Validates: Requirements 6.2**

Property 28: Priority-based queueing
*For any* resource-constrained scenario, the system should use QueueManager to queue incoming requests and process them in priority order
**Validates: Requirements 6.3**

Property 29: Idle conversation timeout
*For any* conversation that becomes idle, the system should implement timeout mechanisms to free resources
**Validates: Requirements 6.4**

### Message Queue Properties

Property 30: Persist-before-acknowledge
*For any* message sent to the queue, the system should persist the message before acknowledging receipt
**Validates: Requirements 7.1**

Property 31: Exponential backoff retry
*For any* message delivery failure, the system should retry delivery with exponential backoff up to a maximum retry count
**Validates: Requirements 7.2**

Property 32: Conversation message ordering
*For any* sequence of messages queued within a conversation, the system should maintain message ordering
**Validates: Requirements 7.3**

Property 33: Message recovery round-trip
*For any* undelivered messages that are persisted, recovering them after a system restart should restore all undelivered messages
**Validates: Requirements 7.4**

Property 34: Backpressure on capacity
*For any* scenario where message queue capacity is reached, the system should apply backpressure and reject new messages with appropriate error codes
**Validates: Requirements 7.5**

### Configuration Management Properties

Property 35: Configuration loading on startup
*For any* system startup, the system should load configuration from a centralized configuration file
**Validates: Requirements 9.1**

Property 36: Hot-reload without restart
*For any* configuration change while the system is running, the system should support hot-reloading without requiring full system restart
**Validates: Requirements 9.2**

Property 37: Configuration validation
*For any* invalid configuration provided, the system should validate configuration and report specific errors
**Validates: Requirements 9.3**

Property 38: Environment-specific overrides
*For any* environment-specific configuration, the system should support environment-specific configuration overrides
**Validates: Requirements 9.4**

Property 39: Type-safe configuration access
*For any* configuration access, the system should provide type-safe configuration access with default values
**Validates: Requirements 9.5**

### Agent-as-Tool Properties

Property 40: Single discovery on initialization
*For any* A2A agent wrapped as a tool, the system should discover the agent card exactly once during initialization
**Validates: Requirements 10.1**

Property 41: Cached instance reuse
*For any* invocation of a wrapped tool, the system should reuse the cached agent card and client instance
**Validates: Requirements 10.2**

Property 42: Multi-agent composition
*For any* set of multiple A2A agent tools, the system should support composing them into a single orchestrator agent
**Validates: Requirements 10.3**

Property 43: Descriptive tool error messages
*For any* A2A agent tool failure, the system should return descriptive error messages including agent name and failure reason
**Validates: Requirements 10.4**

Property 44: Agent card refresh mechanism
*For any* cached agent card, the system should provide a mechanism to refresh the cached card when agent capabilities change
**Validates: Requirements 10.5**

### Analytics Properties

Property 45: Analytics aggregation completeness
*For any* analytics query, the system should provide aggregated metrics by time period, issue type, and outcome
**Validates: Requirements 11.2**

Property 46: Report visualization completeness
*For any* generated report, the system should produce visualizations of key metrics including success rates and average resolution times
**Validates: Requirements 11.3**

Property 47: Pattern identification
*For any* trend analysis, the system should identify patterns in successful negotiations and common failure modes
**Validates: Requirements 11.4**

Property 48: Baseline deviation alerting
*For any* established performance baseline, the system should alert when metrics deviate significantly from baseline values
**Validates: Requirements 11.5**

## Error Handling

### Error Categories

The system handles four categories of errors:

1. **Communication Errors**: A2A protocol failures, network timeouts, agent unavailability
2. **State Errors**: Corruption, inconsistency, persistence failures
3. **Business Logic Errors**: Invalid policy application, negotiation failures, validation errors
4. **Resource Errors**: Queue capacity exceeded, timeout, resource exhaustion

### Error Handling Strategies

#### Communication Error Handling

```python
class A2AErrorHandler:
    """Handles A2A communication errors with retry logic"""
    
    async def handle_communication_error(
        self,
        error: Exception,
        agent_url: str,
        message: str,
        attempt: int
    ) -> ErrorRecoveryAction:
        """
        Determine recovery action for communication errors
        
        Returns:
            - RETRY: Retry with exponential backoff
            - FAILOVER: Try alternate agent instance
            - FAIL: Propagate error to caller
        """
        if isinstance(error, TimeoutError):
            if attempt < MAX_RETRIES:
                return ErrorRecoveryAction.RETRY
            return ErrorRecoveryAction.FAIL
        
        if isinstance(error, ConnectionError):
            # Try to discover alternate agent instance
            if await self.has_failover_agent(agent_url):
                return ErrorRecoveryAction.FAILOVER
            return ErrorRecoveryAction.FAIL
        
        # Unknown error - fail immediately
        return ErrorRecoveryAction.FAIL
```

**Retry Configuration**:
- Initial delay: 100ms
- Backoff factor: 2.0
- Maximum retries: 3
- Maximum delay: 5 seconds

#### State Error Handling

```python
class StateRecoveryManager:
    """Manages conversation state recovery"""
    
    async def recover_corrupted_state(
        self,
        conversation_id: str,
        corrupted_state: Dict[str, Any]
    ) -> ConversationState:
        """
        Recover from corrupted conversation state
        
        Strategy:
        1. Attempt to reconstruct from transaction log
        2. If log is corrupted, reconstruct from message history
        3. If reconstruction fails, create new state with error marker
        """
        try:
            # Try transaction log recovery
            return await self.recover_from_transaction_log(conversation_id)
        except RecoveryError:
            try:
                # Try message history recovery
                return await self.recover_from_message_history(conversation_id)
            except RecoveryError:
                # Create new state with error marker
                return self.create_error_state(conversation_id, corrupted_state)
```

#### Business Logic Error Handling

Business logic errors are handled gracefully with fallback strategies:

- **Invalid Policy**: Return generic policy with explanation
- **Negotiation Failure**: Escalate to human CS representative
- **Validation Error**: Request clarification from customer

#### Resource Error Handling

Resource exhaustion is handled through:

1. **Backpressure**: Reject new requests when capacity is reached
2. **Graceful Degradation**: Reduce service quality (e.g., disable streaming)
3. **Resource Cleanup**: Aggressively timeout idle conversations
4. **Circuit Breaking**: Temporarily disable failing components

### Error Logging and Monitoring

All errors are logged with:
- Error type and message
- Stack trace
- Agent context (ID, current state)
- Conversation context (ID, phase, message count)
- Timestamp and correlation ID

Critical errors trigger alerts through the monitoring system.

## Testing Strategy

### Dual Testing Approach

The system employs both unit testing and property-based testing for comprehensive coverage:

- **Unit tests** verify specific examples, edge cases, and error conditions
- **Property tests** verify universal properties that should hold across all inputs
- Together they provide comprehensive coverage: unit tests catch concrete bugs, property tests verify general correctness

### Property-Based Testing

**Framework**: We will use **Hypothesis** for Python, which is the standard property-based testing library for Python projects.

**Configuration**: Each property-based test will run a minimum of 100 iterations to ensure thorough coverage of the input space.

**Test Tagging**: Each property-based test MUST be tagged with a comment explicitly referencing the correctness property in the design document:

```python
@given(st.text(), st.integers())
def test_property_1_streaming_client_factory(message, agent_id):
    """
    Feature: multi-agent-system-improvements, Property 1: Streaming client factory usage
    
    For any A2A message sent by an agent, the system should use ClientFactory 
    with streaming=True to enable streaming responses
    """
    # Test implementation
    pass
```

**Property Test Requirements**:
- Each correctness property MUST be implemented by a SINGLE property-based test
- Tests MUST use Hypothesis generators to create random test inputs
- Tests MUST verify the property holds across all generated inputs
- Tests MUST be placed close to implementation to catch errors early

### Unit Testing

**Framework**: pytest for Python

**Unit Test Coverage**:
- Specific examples demonstrating correct behavior
- Edge cases (empty inputs, boundary values, null handling)
- Error conditions (invalid inputs, network failures, timeouts)
- Integration points between components

**Example Unit Tests**:

```python
def test_a2a_client_manager_caches_clients():
    """Verify that A2AClientManager caches client instances"""
    manager = A2AClientManager()
    client1 = await manager.get_client("http://localhost:9000")
    client2 = await manager.get_client("http://localhost:9000")
    assert client1 is client2

def test_strategy_selector_handles_empty_history():
    """Verify strategy selection works with empty conversation history"""
    selector = StrategySelector()
    strategy = selector.select_strategy(
        issue_type="damaged_item",
        conversation_history=[],
        cs_sentiment=SentimentScore(0.0, 0.0, 1.0, "neutral"),
        customer_context=CustomerContext()
    )
    assert strategy is not None
    assert strategy.issue_type == "damaged_item"

def test_message_queue_rejects_when_full():
    """Verify message queue applies backpressure at capacity"""
    queue = MessageQueue(max_size=10)
    # Fill queue
    for i in range(10):
        queue.enqueue(Message(f"msg_{i}"))
    
    # Next message should be rejected
    with pytest.raises(QueueFullError):
        queue.enqueue(Message("overflow"))
```

### Integration Testing

Integration tests verify end-to-end workflows:

1. **Full Negotiation Flow**: Customer issue → Context lookup → Negotiation → Resolution
2. **Multi-Agent Communication**: Coordinator → Negotiation → Context with A2A protocol
3. **State Persistence**: Conversation state survives agent restart
4. **Concurrent Conversations**: Multiple customers handled simultaneously
5. **Error Recovery**: System recovers from agent failures

### Performance Testing

Performance tests measure:
- A2A message latency (target: p95 < 500ms)
- Conversation throughput (target: 100 concurrent conversations)
- Memory usage per conversation (target: < 10MB)
- Queue processing rate (target: 1000 messages/second)

### Test Organization

```
tests/
├── unit/
│   ├── test_a2a_client_manager.py
│   ├── test_strategy_selector.py
│   ├── test_policy_ranker.py
│   └── test_message_queue.py
├── property/
│   ├── test_communication_properties.py
│   ├── test_state_properties.py
│   ├── test_negotiation_properties.py
│   └── test_queue_properties.py
├── integration/
│   ├── test_full_negotiation_flow.py
│   ├── test_multi_agent_communication.py
│   └── test_concurrent_conversations.py
└── performance/
    ├── test_latency.py
    └── test_throughput.py
```

### Test Data Generation

For property-based tests, we use Hypothesis strategies to generate:

- **Messages**: Random text content, roles, timestamps
- **Conversation States**: Random conversation IDs, phases, message histories
- **Agent Configurations**: Random ports, URLs, timeout values
- **Policies**: Random policy conditions, actions, priorities
- **CS Responses**: Random sentiment scores, content patterns

### Continuous Testing

Tests run automatically:
- On every commit (unit tests, fast property tests)
- On pull requests (full test suite including integration tests)
- Nightly (extended property tests with 1000+ iterations, performance tests)
