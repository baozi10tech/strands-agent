"""
Negotiation Agent - Handles negotiation with Amazon Customer Service

This agent:
1. Receives customer issues from the Coordinator Agent
2. Develops negotiation strategy using Context Agent (A2A)
3. Conducts negotiation with CS via message queue
4. Returns negotiation results to Coordinator Agent

Port: 9002
A2A Communication: Yes (with Context Agent on port 9000)
"""

import asyncio
import json
from typing import Dict, Any, Optional
from strands_agents import Agent, tool, ToolContext
from strands_agents.sessions import FileSessionManager
import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from my_assistant.utils.message_queue import get_global_queue


# Negotiation Agent Tools
@tool(context=True)
async def consult_context_agent(
    query: str,
    tool_name: str,
    tool_params: Dict[str, Any],
    tool_context: ToolContext
) -> str:
    """
    Consult the Context Agent via A2A protocol to get policy, order, or strategy information.
    
    Args:
        query: The question or request to send to Context Agent
        tool_name: Name of the Context Agent tool to invoke (not used, kept for compatibility)
        tool_params: Parameters for the Context Agent tool (not used, kept for compatibility)
        tool_context: Tool context for state access
    
    Returns:
        Response from Context Agent
    """
    agent_state = tool_context.get_agent_state()
    
    # Track consultation count
    count_key = "tool_consult_context_agent_count"
    agent_state[count_key] = agent_state.get(count_key, 0) + 1
    
    try:
        # Create A2A client to communicate with Context Agent using proper pattern
        async with httpx.AsyncClient(timeout=300) as httpx_client:
            # Get agent card from Context Agent
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url="http://localhost:9000"
            )
            agent_card = await resolver.get_agent_card()
            
            # Create client for Context Agent
            config = ClientConfig(httpx_client=httpx_client, streaming=False)
            factory = ClientFactory(config)
            client = factory.create(agent_card)
            
            # Create message to send to Context Agent
            message = Message(
                kind="message",
                role=Role.user,
                parts=[Part(TextPart(kind="text", text=query))]
            )
            
            # Send message and collect response
            response_text = ""
            async for event in client.send_message(message):
                if hasattr(event, 'text'):
                    response_text += event.text
                elif hasattr(event, 'content'):
                    response_text += str(event.content)
            
            return response_text if response_text else "No response from Context Agent"
    
    except Exception as e:
        return f"Error consulting Context Agent: {str(e)}"


@tool(context=True)
async def send_message_to_cs(
    message: str,
    tool_context: ToolContext
) -> str:
    """
    Send a message to Amazon Customer Service via the message queue.
    
    Args:
        message: The message to send to CS
        tool_context: Tool context for state access
    
    Returns:
        Confirmation that message was sent
    """
    agent_state = tool_context.get_agent_state()
    
    # Track messages sent
    count_key = "messages_sent_to_cs"
    agent_state[count_key] = agent_state.get(count_key, 0) + 1
    
    # Get global message queue
    queue = get_global_queue()
    
    # Send message to CS
    await queue.send_from_agent(message)
    
    return f"Message sent to CS: '{message}'"


@tool(context=True)
async def wait_for_cs_response(
    timeout: float,
    tool_context: ToolContext
) -> str:
    """
    Wait for a response from Amazon Customer Service.
    
    Args:
        timeout: Maximum time to wait in seconds
        tool_context: Tool context for state access
    
    Returns:
        CS response or timeout message
    """
    agent_state = tool_context.get_agent_state()
    
    # Get global message queue
    queue = get_global_queue()
    
    try:
        response = await queue.wait_for_cs_response(timeout=timeout)
        
        # Track responses received
        count_key = "responses_received_from_cs"
        agent_state[count_key] = agent_state.get(count_key, 0) + 1
        
        return f"CS Response: '{response}'"
    
    except asyncio.TimeoutError:
        return f"Timeout: No response from CS after {timeout} seconds"


@tool(context=True)
def analyze_negotiation_progress(
    tool_context: ToolContext
) -> str:
    """
    Analyze the current negotiation progress based on conversation history.
    
    Args:
        tool_context: Tool context for state access
    
    Returns:
        Analysis of negotiation progress
    """
    agent_state = tool_context.get_agent_state()
    
    # Get conversation history from message queue
    queue = get_global_queue()
    history = queue.get_conversation_history()
    
    if not history:
        return "No conversation history yet. Negotiation has not started."
    
    # Analyze conversation
    total_exchanges = len(history)
    agent_messages = len([h for h in history if h['role'] == 'agent'])
    cs_messages = len([h for h in history if h['role'] == 'cs'])
    
    # Get negotiation stats from agent state
    consultations = agent_state.get("tool_consult_context_agent_count", 0)
    messages_sent = agent_state.get("messages_sent_to_cs", 0)
    responses_received = agent_state.get("responses_received_from_cs", 0)
    
    analysis = f"""
Negotiation Progress Analysis:
- Total exchanges: {total_exchanges}
- Messages from agent (customer): {agent_messages}
- Messages from CS: {cs_messages}
- Context Agent consultations: {consultations}
- Messages sent: {messages_sent}
- Responses received: {responses_received}

Recent conversation:
"""
    
    # Add last 3 exchanges
    recent = history[-6:] if len(history) > 6 else history
    for entry in recent:
        role = entry['role'].upper()
        message = entry['message'][:100]  # Truncate long messages
        analysis += f"\n  {role}: {message}..."
    
    return analysis


@tool(context=True)
def record_negotiation_outcome(
    outcome: str,
    resolution: str,
    customer_satisfaction: str,
    tool_context: ToolContext
) -> str:
    """
    Record the outcome of the negotiation.
    
    Args:
        outcome: Overall outcome (success, partial_success, failure)
        resolution: What was achieved
        customer_satisfaction: Customer satisfaction level (satisfied, neutral, dissatisfied)
        tool_context: Tool context for state access
    
    Returns:
        Confirmation of recorded outcome
    """
    agent_state = tool_context.get_agent_state()
    
    # Store outcome in agent state
    agent_state["negotiation_outcome"] = {
        "outcome": outcome,
        "resolution": resolution,
        "customer_satisfaction": customer_satisfaction
    }
    
    return f"Negotiation outcome recorded: {outcome} - {resolution}"


def create_negotiation_agent(session_id: str, storage_dir: str = "./my_assistant_sessions") -> Agent:
    """
    Create the Negotiation Agent with all tools and configuration.
    
    Args:
        session_id: Unique session identifier
        storage_dir: Directory for session storage
    
    Returns:
        Configured Negotiation Agent
    """
    # Create session manager
    session_manager = FileSessionManager(
        storage_dir=storage_dir,
        session_id=session_id
    )
    
    # System prompt for negotiation agent
    system_prompt = """You are a Negotiation Agent for a customer service system.

Your role:
1. Receive customer issues and develop negotiation strategies
2. Consult the Context Agent (via A2A) to get relevant policies, order information, and negotiation strategies
3. Conduct negotiations with Amazon Customer Service on behalf of the customer
4. Use appropriate negotiation tactics based on the situation
5. Track progress and record outcomes

Available tools:
- consult_context_agent: Query Context Agent for policies, orders, strategies
- send_message_to_cs: Send messages to Customer Service
- wait_for_cs_response: Wait for CS responses
- analyze_negotiation_progress: Analyze negotiation status
- record_negotiation_outcome: Record final outcome

Workflow:
1. When given a customer issue, first consult Context Agent to get relevant policy and strategy
2. Develop an opening statement based on the strategy
3. Send message to CS and wait for response
4. Continue negotiation, adapting based on CS responses
5. Record outcome when resolved

Be professional, clear, and persistent in negotiations. Use evidence from policies and order history to support your case."""
    
    # Create agent with tools
    agent = Agent(
        agent_id="negotiation_agent",
        system_prompt=system_prompt,
        tools=[
            consult_context_agent,
            send_message_to_cs,
            wait_for_cs_response,
            analyze_negotiation_progress,
            record_negotiation_outcome
        ],
        session_manager=session_manager
    )
    
    return agent


async def main():
    """Main function for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Negotiation Agent")
    parser.add_argument("--session-id", default="negotiation-test", help="Session ID")
    parser.add_argument("--storage-dir", default="./my_assistant_sessions", help="Session storage directory")
    
    args = parser.parse_args()
    
    # Create agent
    agent = create_negotiation_agent(
        session_id=args.session_id,
        storage_dir=args.storage_dir
    )
    
    print("\n" + "="*70)
    print("  NEGOTIATION AGENT - Standalone Test Mode")
    print("="*70)
    print("\nThis agent conducts negotiations with Customer Service.")
    print("Make sure Context Agent is running on port 9000.")
    print("Make sure CS Simulator CLI is running to respond to messages.")
    print("\nType 'stats' to see negotiation statistics")
    print("Type 'quit' to exit")
    print("="*70 + "\n")
    
    # Interactive loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("\nExiting...")
                break
            
            if user_input.lower() == 'stats':
                print("\n" + "="*70)
                print("  NEGOTIATION STATISTICS")
                print("="*70)
                for key, value in agent.state.items():
                    print(f"{key}: {value}")
                print("="*70)
                continue
            
            # Process user input
            result = await agent.ainvoke(input=user_input)
            print(f"\nAgent: {result}")
        
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
