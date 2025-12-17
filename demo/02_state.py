import argparse
import json
from strands import Agent, tool, ToolContext
from strands.agent.conversation_manager import NullConversationManager, SlidingWindowConversationManager

@tool(context=True)
def get_policy(issue: str, tool_context: ToolContext) -> str:
    """Get policy information"""
    # set the tool invocation count
    tool_get_policy_count = tool_context.agent.state.get("tool_get_policy_count") or 0
    tool_context.agent.state.set("tool_get_policy_count",  tool_get_policy_count + 1)

    policies = {
        "return": "30-Day Return Policy: Items can be returned within 30 days for full refund",
        "refund": "Refund Processing: Refunds processed within 5-7 business days",
        "damaged item": "Damaged Items: Immediate replacement or full refund for damaged items"
    }
    return policies.get(issue, f"Policy {issue} not found")

def custom_callback_handler(**kwargs):
    # Access request state
    print("--" * 60)
    print(f"Event args: {kwargs}")
    if "request_state" in kwargs:
        state = kwargs["request_state"]
        print(f"Request state: {state}")

def create_agent(conversation_manager=None, callback_handler=None) -> Agent:
    system_prompt = "You are a Context Agent for customer service. " \
    "When customers ask about questions, try to look up the relevant policy. "     
    agent = Agent(
        system_prompt=system_prompt,
        tools=[get_policy],
        state={},
        conversation_manager=conversation_manager,
        callback_handler=callback_handler
    )
    
    return agent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--window-size', type=int, help='Window size for conversation manager')
    parser.add_argument('--agent-state', action='store_true', help='Agent state')
    parser.add_argument('--request-state', action='store_true', help='Request state')
    args = parser.parse_args()
    
    if args.window_size:
        agent = create_agent(conversation_manager=SlidingWindowConversationManager(
            window_size=args.window_size,
            should_truncate_results=True
            ))
        agent("I have a item bought 45 days ago. can I return it?")
        agent("how to contact customer service")
        agent("when did I get the my item that I wanted to return?")
        print()
        print("--" * 60)
        print("Agent message length: ")
        print(len(agent.messages))
        print(json.dumps(agent.messages, indent=2))
        agent.cleanup()
    elif args.agent_state:
        agent = create_agent()
        agent("I have a item bought 45 days ago. can I return it?")
        agent("how to contact customer service")
        agent("when did I get the my item that I wanted to return?")
        print()
        print("--" * 60)
        print("Agent state --> tool invokation count: ")
        print(agent.state.get("tool_get_policy_count"))
        agent.cleanup()
    elif args.request_state:
        agent = create_agent(callback_handler=custom_callback_handler)
        agent("I have a item bought 45 days ago. can I return it?")
        print()
        agent.cleanup() 
    else:
        agent = create_agent(conversation_manager=NullConversationManager())
        agent("I have a item bought 45 days ago. can I return it?")
        agent("how to contact customer service")
        agent("when did I get the my item that I wanted to return?")
        print()
        print("--" * 60)
        print("Agent message length and content: ")
        print(len(agent.messages))
        print(json.dumps(agent.messages, indent=2))
        agent.cleanup()

if __name__ == "__main__":
    main()
