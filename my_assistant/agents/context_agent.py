"""
Context Agent - Intelligent Knowledge Base (Port 9000)

This agent provides:
- Policy lookup and interpretation
- Order data retrieval and analysis
- Negotiation strategy recommendations
- Action validation against policies
- LLM-powered reasoning for complex queries

Based on demo techniques:
- Agent loop with tools (demo 01)
- Agent state tracking (demo 02)
- Session persistence (demo 03)
- Guardrails for sensitive data (demo 04)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from strands import Agent, tool, ToolContext
from strands.session.file_session_manager import FileSessionManager


# Load mock data
DATA_DIR = Path(__file__).parent.parent / "data"

def load_json_data(filename: str) -> dict:
    """Load JSON data file"""
    filepath = DATA_DIR / filename
    with open(filepath, 'r') as f:
        return json.load(f)

# Load data at module level
POLICIES = load_json_data("policies.json")
ORDERS = load_json_data("orders.json")
STRATEGIES = load_json_data("strategies.json")


# Tool definitions with agent state tracking

@tool(context=True)
def get_policy(policy_name: str, tool_context: ToolContext) -> str:
    """
    Retrieve specific policy details by policy ID or name.
    
    Args:
        policy_name: Policy ID (e.g., 'P-247') or partial name (e.g., 'damaged')
    
    Returns:
        JSON string with policy details or error message
    """
    # Track tool usage in agent state
    tool_count = tool_context.agent.state.get("tool_get_policy_count") or 0
    tool_context.agent.state.set("tool_get_policy_count", tool_count + 1)
    
    # Direct lookup by policy ID
    if policy_name in POLICIES:
        policy = POLICIES[policy_name]
        return json.dumps(policy, indent=2)
    
    # Search by partial name (case-insensitive)
    policy_name_lower = policy_name.lower()
    for policy_id, policy_data in POLICIES.items():
        if (policy_name_lower in policy_data['name'].lower() or 
            policy_name_lower in policy_data['description'].lower() or
            policy_name_lower in policy_data['category'].lower()):
            return json.dumps(policy_data, indent=2)
    
    return json.dumps({
        "error": f"Policy '{policy_name}' not found",
        "available_policies": list(POLICIES.keys())
    }, indent=2)


@tool(context=True)
def search_policies(query: str, tool_context: ToolContext) -> str:
    """
    Search policies by keyword across name, description, category, conditions, and actions.
    
    Args:
        query: Search term (e.g., 'refund', 'damaged', 'prime')
    
    Returns:
        JSON string with list of matching policies
    """
    # Track tool usage
    tool_count = tool_context.agent.state.get("tool_search_policies_count") or 0
    tool_context.agent.state.set("tool_search_policies_count", tool_count + 1)
    
    query_lower = query.lower()
    matching_policies = []
    
    for policy_id, policy_data in POLICIES.items():
        # Search in all text fields
        searchable_text = (
            policy_data['name'] + ' ' +
            policy_data['description'] + ' ' +
            policy_data['category'] + ' ' +
            ' '.join(policy_data['conditions']) + ' ' +
            ' '.join(policy_data['actions']) + ' ' +
            policy_data['timeframe']
        ).lower()
        
        if query_lower in searchable_text:
            matching_policies.append({
                "policy_id": policy_id,
                "name": policy_data['name'],
                "description": policy_data['description'],
                "category": policy_data['category']
            })
    
    if not matching_policies:
        return json.dumps({
            "message": f"No policies found matching '{query}'",
            "total": 0,
            "results": []
        }, indent=2)
    
    return json.dumps({
        "message": f"Found {len(matching_policies)} policies matching '{query}'",
        "total": len(matching_policies),
        "results": matching_policies
    }, indent=2)


@tool(context=True)
def get_order(order_id: str, tool_context: ToolContext) -> str:
    """
    Retrieve order information by order ID.
    
    Args:
        order_id: Order ID (e.g., '123-4567890-1234567')
    
    Returns:
        JSON string with order details or error message
    """
    # Track tool usage
    tool_count = tool_context.agent.state.get("tool_get_order_count") or 0
    tool_context.agent.state.set("tool_get_order_count", tool_count + 1)
    
    if order_id in ORDERS:
        order = ORDERS[order_id]
        return json.dumps(order, indent=2)
    
    return json.dumps({
        "error": f"Order '{order_id}' not found",
        "available_orders": list(ORDERS.keys())
    }, indent=2)


@tool(context=True)
def get_customer_history(customer_id: Optional[str] = None, tool_context: ToolContext = None) -> str:
    """
    Get customer's order history. If no customer_id provided, returns all orders.
    
    Args:
        customer_id: Customer ID (e.g., 'C-12345')
    
    Returns:
        JSON string with list of customer orders
    """
    # Track tool usage
    tool_count = tool_context.agent.state.get("tool_get_customer_history_count") or 0
    tool_context.agent.state.set("tool_get_customer_history_count", tool_count + 1)
    
    customer_orders = []
    
    for order_id, order_data in ORDERS.items():
        if customer_id is None or order_data['customer_id'] == customer_id:
            customer_orders.append({
                "order_id": order_id,
                "order_date": order_data['order_date'],
                "status": order_data['status'],
                "total_amount": order_data['total_amount'],
                "is_prime": order_data['is_prime'],
                "items_count": len(order_data['items'])
            })
    
    return json.dumps({
        "customer_id": customer_id or "all",
        "total_orders": len(customer_orders),
        "orders": customer_orders
    }, indent=2)


@tool(context=True)
def recommend_strategy(issue_type: str, tool_context: ToolContext) -> str:
    """
    Get negotiation strategy recommendations for specific issue type.
    
    Args:
        issue_type: Type of issue (e.g., 'damaged_item', 'late_delivery', 'wrong_item')
    
    Returns:
        JSON string with strategy details or error message
    """
    # Track tool usage
    tool_count = tool_context.agent.state.get("tool_recommend_strategy_count") or 0
    tool_context.agent.state.set("tool_recommend_strategy_count", tool_count + 1)
    
    # Direct lookup
    if issue_type in STRATEGIES:
        strategy = STRATEGIES[issue_type]
        return json.dumps(strategy, indent=2)
    
    # Try to match partial issue type
    issue_type_lower = issue_type.lower().replace(' ', '_')
    for strategy_key, strategy_data in STRATEGIES.items():
        if issue_type_lower in strategy_key or strategy_key in issue_type_lower:
            return json.dumps(strategy_data, indent=2)
    
    return json.dumps({
        "error": f"No strategy found for issue type '{issue_type}'",
        "available_strategies": list(STRATEGIES.keys())
    }, indent=2)


@tool(context=True)
def validate_action(action_type: str, params: dict, tool_context: ToolContext) -> str:
    """
    Validate if a proposed action is allowed by policies.
    
    Args:
        action_type: Type of action (e.g., 'refund', 'return_label', 'credit')
        params: Action parameters (e.g., {'amount': 999.99, 'policy_id': 'P-247'})
    
    Returns:
        JSON string with validation result
    """
    # Track tool usage
    tool_count = tool_context.agent.state.get("tool_validate_action_count") or 0
    tool_context.agent.state.set("tool_validate_action_count", tool_count + 1)
    
    validation_result = {
        "action_type": action_type,
        "params": params,
        "valid": False,
        "reason": "",
        "policy_reference": None
    }
    
    # Validate based on action type
    if action_type == "refund":
        if "policy_id" in params and params["policy_id"] in POLICIES:
            policy = POLICIES[params["policy_id"]]
            # Check if refund is mentioned in policy actions
            refund_action = any("refund" in action.lower() for action in policy['actions'])
            validation_result["valid"] = refund_action
            validation_result["policy_reference"] = params["policy_id"]
            validation_result["reason"] = f"Refund is {'allowed' if refund_action else 'not mentioned'} in policy {params['policy_id']}"
        else:
            validation_result["reason"] = "Policy ID not provided or invalid"
    
    elif action_type == "return_label":
        if "policy_id" in params and params["policy_id"] in POLICIES:
            policy = POLICIES[params["policy_id"]]
            label_action = any("return label" in action.lower() or "prepaid" in action.lower() 
                             for action in policy['actions'])
            validation_result["valid"] = label_action
            validation_result["policy_reference"] = params["policy_id"]
            validation_result["reason"] = f"Return label is {'allowed' if label_action else 'not mentioned'} in policy {params['policy_id']}"
        else:
            validation_result["reason"] = "Policy ID not provided or invalid"
    
    elif action_type == "credit":
        if "policy_id" in params and params["policy_id"] in POLICIES:
            policy = POLICIES[params["policy_id"]]
            credit_action = any("credit" in action.lower() for action in policy['actions'])
            validation_result["valid"] = credit_action
            validation_result["policy_reference"] = params["policy_id"]
            validation_result["reason"] = f"Credit is {'allowed' if credit_action else 'not mentioned'} in policy {params['policy_id']}"
        else:
            validation_result["reason"] = "Policy ID not provided or invalid"
    
    else:
        validation_result["reason"] = f"Unknown action type: {action_type}"
    
    return json.dumps(validation_result, indent=2)


def create_context_agent(session_id: Optional[str] = None, 
                         storage_dir: str = "./my_assistant_sessions") -> Agent:
    """
    Create the Context Agent with all tools and configuration.
    
    Args:
        session_id: Optional session ID for persistence
        storage_dir: Directory to store session files
    
    Returns:
        Configured Agent instance
    """
    system_prompt = """You are a Context Agent for a customer service system.

Your role is to provide intelligent knowledge base access for:
- Amazon customer service policies
- Customer order information
- Negotiation strategies
- Action validation

When queried, use your tools to:
1. Look up relevant policies by ID or keyword
2. Retrieve order details and customer history
3. Recommend appropriate negotiation strategies
4. Validate proposed actions against policies

Provide clear, accurate information to help resolve customer issues effectively.
Always reference specific policy IDs when applicable.
Be thorough in your responses and consider multiple relevant policies."""

    # Set up session manager if session_id provided
    session_manager = None
    if session_id:
        session_manager = FileSessionManager(
            session_id=session_id,
            storage_dir=storage_dir
        )
    
    # Create agent with all tools
    agent = Agent(
        system_prompt=system_prompt,
        tools=[
            get_policy,
            search_policies,
            get_order,
            get_customer_history,
            recommend_strategy,
            validate_action
        ],
        state={},  # Initialize empty state for tracking
        session_manager=session_manager
    )
    
    return agent


def main():
    """
    Main function for testing Context Agent standalone.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Context Agent - Intelligent Knowledge Base")
    parser.add_argument('--session-id', type=str, help='Session ID for persistence')
    parser.add_argument('--storage-dir', type=str, default='./my_assistant_sessions',
                       help='Directory to store session files')
    args = parser.parse_args()
    
    # Create agent
    agent = create_context_agent(
        session_id=args.session_id,
        storage_dir=args.storage_dir
    )
    
    print("=" * 80)
    print("Context Agent - Intelligent Knowledge Base (Port 9000)")
    print("=" * 80)
    if args.session_id:
        print(f"Session ID: {args.session_id}")
    print("\nAvailable commands:")
    print("  - Ask about policies (e.g., 'What's the damaged item policy?')")
    print("  - Query orders (e.g., 'Get order 123-4567890-1234567')")
    print("  - Request strategies (e.g., 'Strategy for late delivery')")
    print("  - Validate actions (e.g., 'Can I refund under policy P-247?')")
    print("  - Type 'stats' to see tool usage statistics")
    print("  - Type 'quit' to exit")
    print("=" * 80)
    print()
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if user_input.lower() == 'stats':
            print("\n--- Tool Usage Statistics ---")
            print(f"get_policy: {agent.state.get('tool_get_policy_count') or 0}")
            print(f"search_policies: {agent.state.get('tool_search_policies_count') or 0}")
            print(f"get_order: {agent.state.get('tool_get_order_count') or 0}")
            print(f"get_customer_history: {agent.state.get('tool_get_customer_history_count') or 0}")
            print(f"recommend_strategy: {agent.state.get('tool_recommend_strategy_count') or 0}")
            print(f"validate_action: {agent.state.get('tool_validate_action_count') or 0}")
            print()
            continue
        
        if not user_input:
            continue
        
        print("-" * 80)
        print("Agent: ", end="", flush=True)
        agent(user_input)
        print()
        print("-" * 80)
        print()
    
    agent.cleanup()


if __name__ == "__main__":
    main()
