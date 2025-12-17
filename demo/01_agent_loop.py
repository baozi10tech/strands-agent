"""Checkpoint 1: Agent Loop - Basic Context Agent with simple policy lookup tool"""

from strands import Agent, tool

@tool
def get_policy(issue: str) -> str:
    """Get policy information by ID"""
    policies = {
        "return": "30-Day Return Policy: Items can be returned within 30 days for full refund",
        "refund": "Refund Processing: Refunds processed within 5-7 business days",
        "damaged item": "Damaged Items: Immediate replacement or full refund for damaged items"
    }
    return policies.get(issue, f"Policy {issue} not found")


def create_agent() -> Agent:
    system_prompt = "You are a Context Agent for customer service. " \
    "When customers ask about questions, try to look up the relevant policy"
    
    agent = Agent(
        system_prompt=system_prompt,
        tools=[get_policy],
    )
    
    return agent

def main():    
    agent = create_agent()
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
            
        if not user_input:
            continue
        
        print("--" * 60)
        print("\nAgent: ", end="", flush=True)
        agent(user_input)
        print()
        print("--" * 60)
        

if __name__ == "__main__":
    main()