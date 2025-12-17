"""
Coordinator Agent - Main orchestrator for the customer service system

This agent:
1. Receives customer issues from the Customer CLI
2. Analyzes the issue and determines the appropriate action
3. Delegates to Negotiation Agent via A2A
4. Monitors progress and provides updates to customer
5. Returns final resolution to customer

Port: 9001
A2A Communication: Yes (with Negotiation Agent on port 9002)
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


# Coordinator Agent Tools
@tool(context=True)
async def delegate_to_negotiation_agent(
    issue_description: str,
    order_id: Optional[str],
    customer_id: Optional[str],
    tool_context: ToolContext
) -> str:
    """
    Delegate customer issue to the Negotiation Agent via A2A protocol.
    
    Args:
        issue_description: Description of the customer's issue
        order_id: Optional order ID related to the issue
        customer_id: Optional customer ID
        tool_context: Tool context for state access
    
    Returns:
        Response from Negotiation Agent with negotiation outcome
    """
    agent_state = tool_context.get_agent_state()
    
    # Track delegations
    count_key = "tool_delegate_to_negotiation_agent_count"
    agent_state[count_key] = agent_state.get(count_key, 0) + 1
    
    # Store current issue being handled
    agent_state["current_issue"] = {
        "description": issue_description,
        "order_id": order_id,
        "customer_id": customer_id
    }
    
    try:
        # Build delegation message
        delegation_message = f"""Customer Issue Delegation:

Issue: {issue_description}
Order ID: {order_id or 'Not provided'}
Customer ID: {customer_id or 'Not provided'}

Please handle this negotiation with Customer Service. Use the Context Agent to gather relevant policies and strategies, then conduct the negotiation."""
        
        # Create A2A client to communicate with Negotiation Agent using proper pattern
        async with httpx.AsyncClient(timeout=300) as httpx_client:
            # Get agent card from Negotiation Agent
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url="http://localhost:9002"
            )
            agent_card = await resolver.get_agent_card()
            
            # Create client for Negotiation Agent
            config = ClientConfig(httpx_client=httpx_client, streaming=False)
            factory = ClientFactory(config)
            client = factory.create(agent_card)
            
            # Create message to send to Negotiation Agent
            message = Message(
                kind="message",
                role=Role.user,
                parts=[Part(TextPart(kind="text", text=delegation_message))]
            )
            
            # Send message and collect response
            response_text = ""
            async for event in client.send_message(message):
                if hasattr(event, 'text'):
                    response_text += event.text
                elif hasattr(event, 'content'):
                    response_text += str(event.content)
            
            return response_text if response_text else "No response from Negotiation Agent"
    
    except Exception as e:
        return f"Error delegating to Negotiation Agent: {str(e)}"


@tool(context=True)
async def check_negotiation_status(
    tool_context: ToolContext
) -> str:
    """
    Check the status of ongoing negotiation with the Negotiation Agent.
    
    Args:
        tool_context: Tool context for state access
    
    Returns:
        Current status of the negotiation
    """
    agent_state = tool_context.get_agent_state()
    
    # Track status checks
    count_key = "tool_check_negotiation_status_count"
    agent_state[count_key] = agent_state.get(count_key, 0) + 1
    
    current_issue = agent_state.get("current_issue", None)
    
    if not current_issue:
        return "No active negotiation in progress."
    
    try:
        # Request status update
        status_request = "Please provide a status update on the current negotiation."
        
        # Create A2A client to communicate with Negotiation Agent using proper pattern
        async with httpx.AsyncClient(timeout=300) as httpx_client:
            # Get agent card from Negotiation Agent
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url="http://localhost:9002"
            )
            agent_card = await resolver.get_agent_card()
            
            # Create client for Negotiation Agent
            config = ClientConfig(httpx_client=httpx_client, streaming=False)
            factory = ClientFactory(config)
            client = factory.create(agent_card)
            
            # Create message to send to Negotiation Agent
            message = Message(
                kind="message",
                role=Role.user,
                parts=[Part(TextPart(kind="text", text=status_request))]
            )
            
            # Send message and collect response
            response_text = ""
            async for event in client.send_message(message):
                if hasattr(event, 'text'):
                    response_text += event.text
                elif hasattr(event, 'content'):
                    response_text += str(event.content)
            
            return response_text if response_text else "No status update available"
    
    except Exception as e:
        return f"Error checking negotiation status: {str(e)}"


@tool(context=True)
def analyze_customer_issue(
    issue_description: str,
    tool_context: ToolContext
) -> str:
    """
    Analyze customer issue to determine issue type and suggested approach.
    
    Args:
        issue_description: Description of the customer's issue
        tool_context: Tool context for state access
    
    Returns:
        Analysis with issue type and recommended approach
    """
    agent_state = tool_context.get_agent_state()
    
    # Track analysis count
    count_key = "tool_analyze_customer_issue_count"
    agent_state[count_key] = agent_state.get(count_key, 0) + 1
    
    # Simple keyword-based analysis
    issue_lower = issue_description.lower()
    
    issue_type = "general"
    keywords_found = []
    
    # Detect issue type based on keywords
    if any(word in issue_lower for word in ["damaged", "broken", "defective", "not working"]):
        issue_type = "damaged_item"
        keywords_found.append("damaged/defective")
    
    if any(word in issue_lower for word in ["late", "delayed", "hasn't arrived", "not delivered"]):
        issue_type = "late_delivery"
        keywords_found.append("delayed delivery")
    
    if any(word in issue_lower for word in ["wrong", "incorrect", "different item", "not what i ordered"]):
        issue_type = "wrong_item"
        keywords_found.append("wrong item")
    
    if any(word in issue_lower for word in ["return", "refund", "send back"]):
        issue_type = "return_standard"
        keywords_found.append("return/refund")
    
    if any(word in issue_lower for word in ["missing", "never received", "lost", "stolen"]):
        issue_type = "missing_package"
        keywords_found.append("missing package")
    
    analysis = f"""
Customer Issue Analysis:
- Issue Type: {issue_type}
- Keywords Found: {', '.join(keywords_found) if keywords_found else 'None'}
- Recommended Approach: Delegate to Negotiation Agent for resolution

Next Steps:
1. Use delegate_to_negotiation_agent to handle this issue
2. The Negotiation Agent will consult Context Agent for relevant policies
3. The Negotiation Agent will conduct negotiation with CS
4. Monitor progress with check_negotiation_status if needed
"""
    
    return analysis


@tool(context=True)
def record_case_resolution(
    resolution_summary: str,
    customer_satisfied: bool,
    tool_context: ToolContext
) -> str:
    """
    Record the final resolution of the customer case.
    
    Args:
        resolution_summary: Summary of how the case was resolved
        customer_satisfied: Whether customer was satisfied with resolution
        tool_context: Tool context for state access
    
    Returns:
        Confirmation of recorded resolution
    """
    agent_state = tool_context.get_agent_state()
    
    # Store resolution in agent state
    agent_state["case_resolution"] = {
        "summary": resolution_summary,
        "customer_satisfied": customer_satisfied
    }
    
    # Clear current issue
    if "current_issue" in agent_state:
        del agent_state["current_issue"]
    
    return f"Case resolution recorded. Customer satisfaction: {'Yes' if customer_satisfied else 'No'}"


def create_coordinator_agent(session_id: str, storage_dir: str = "./my_assistant_sessions") -> Agent:
    """
    Create the Coordinator Agent with all tools and configuration.
    
    Args:
        session_id: Unique session identifier
        storage_dir: Directory for session storage
    
    Returns:
        Configured Coordinator Agent
    """
    # Create session manager
    session_manager = FileSessionManager(
        storage_dir=storage_dir,
        session_id=session_id
    )
    
    # System prompt for coordinator agent
    system_prompt = """You are a Coordinator Agent for an AI-powered customer service system.

Your role:
1. Receive customer service issues from customers
2. Analyze the issue to understand the problem type
3. Delegate to the Negotiation Agent (via A2A) to handle the negotiation with CS
4. Monitor progress and provide updates to the customer
5. Record final resolution and customer satisfaction

Available tools:
- analyze_customer_issue: Analyze the customer's issue to determine type and approach
- delegate_to_negotiation_agent: Send the issue to Negotiation Agent for handling
- check_negotiation_status: Check progress of ongoing negotiation
- record_case_resolution: Record the final outcome

Workflow:
1. When a customer describes an issue, first analyze it with analyze_customer_issue
2. Delegate to Negotiation Agent using delegate_to_negotiation_agent
3. The Negotiation Agent will handle the entire negotiation process with CS
4. Monitor if needed with check_negotiation_status
5. When resolved, record the outcome with record_case_resolution

Be empathetic, professional, and ensure the customer feels heard. Keep the customer informed throughout the process."""
    
    # Create agent with tools
    agent = Agent(
        agent_id="coordinator_agent",
        system_prompt=system_prompt,
        tools=[
            analyze_customer_issue,
            delegate_to_negotiation_agent,
            check_negotiation_status,
            record_case_resolution
        ],
        session_manager=session_manager
    )
    
    return agent


async def main():
    """Main function for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Coordinator Agent")
    parser.add_argument("--session-id", default="coordinator-test", help="Session ID")
    parser.add_argument("--storage-dir", default="./my_assistant_sessions", help="Session storage directory")
    
    args = parser.parse_args()
    
    # Create agent
    agent = create_coordinator_agent(
        session_id=args.session_id,
        storage_dir=args.storage_dir
    )
    
    print("\n" + "="*70)
    print("  COORDINATOR AGENT - Standalone Test Mode")
    print("="*70)
    print("\nThis agent coordinates customer service requests.")
    print("Make sure Negotiation Agent is running on port 9002.")
    print("\nType 'stats' to see coordination statistics")
    print("Type 'quit' to exit")
    print("="*70 + "\n")
    
    # Interactive loop
    while True:
        try:
            user_input = input("\nCustomer: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("\nExiting...")
                break
            
            if user_input.lower() == 'stats':
                print("\n" + "="*70)
                print("  COORDINATION STATISTICS")
                print("="*70)
                for key, value in agent.state.items():
                    print(f"{key}: {value}")
                print("="*70)
                continue
            
            # Process customer input
            result = await agent.ainvoke(input=user_input)
            print(f"\nCoordinator: {result}")
        
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
