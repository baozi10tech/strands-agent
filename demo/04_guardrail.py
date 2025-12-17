import argparse
from strands import Agent, tool, ToolContext
from strands.session.file_session_manager import FileSessionManager
from strands.models import BedrockModel

@tool(context=True)
def get_policy(issue: str, tool_context: ToolContext) -> str:
    """Get policy information and track customer details"""
    policies = {
        "return": "30-Day Return Policy: Items can be returned within 30 days for full refund",
        "refund": "Refund Processing: Refunds processed within 5-7 business days",
        "damaged item": "Damaged Items: Immediate replacement or full refund for damaged items"
    }
    return policies.get(issue, f"Policy {issue} not found")

def create_agent(session_manager) -> Agent:
    system_prompt = (
        "You are a Context Agent for customer service. "
        "Look up relevant policies when needed."
    )

    # Create a Bedrock model with guardrail configuration
    bedrock_model = BedrockModel(
        model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
        guardrail_id="xxuqm2u2t7sq",
        guardrail_version="4",
        guardrail_trace="enabled",
        region_name="us-east-2",
    )

    
    agent = Agent(
        system_prompt=system_prompt,
        tools=[get_policy],
        session_manager=session_manager,
        model=bedrock_model
    )
    
    return agent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session-id', type=str, 
                       default='customer-session',
                       help='Session ID for persistence')
    parser.add_argument('--storage-dir', type=str,
                       default='./demo_sessions',
                       help='Directory to store session files')
    args = parser.parse_args()
    
    session_manager = FileSessionManager(
        session_id=args.session_id,
        storage_dir=args.storage_dir
    )
    
    agent = create_agent(session_manager)
    
    print("-" * 60)
    print(f"Session ID: {args.session_id}")
    print("=" * 80)
    print()
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye! Session saved.")
            break
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
