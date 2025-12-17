import re
from strands import Agent, tool
from strands.hooks import HookProvider, HookRegistry, AfterInvocationEvent

import logging

logging.basicConfig(level=logging.WARNING) 

class EmailMaskingHook(HookProvider):
    def __init__(self):
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
    
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(AfterInvocationEvent, self.mask_emails)
    
    def mask_emails(self, event: AfterInvocationEvent) -> None:
        if not event.agent.messages:
            return
        
        # print(">>>>>>>>>>>>>>")
        # print(event.agent.messages[-1]["content"][0]["text"])
        event.agent.messages[-1]["content"][0]["text"] = self.email_pattern.sub(
            '[MASKED_EMAIL_HOOK]', event.agent.messages[-1]["content"][0]["text"]
        )
        # print(event.agent.messages[-1]["content"][0]["text"])
        
        


@tool
def get_policy(issue: str) -> str:
    """Get customer service policy for an issue"""
    policies = {
        "return": "30-day return policy for unopened items",
        "refund": "Full refund within 14 days of return",
        "damaged item": "Report within 48 hours for replacement",
        "shipping delay": "Contact support if delayed more than 5 business days"
    }
    return policies.get(issue.lower(), "No policy found for this issue")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Checkpoint 05: Hooks Demo")
    parser.add_argument('--no-mask', action='store_true', 
                       help='Disable email masking hook')
    args = parser.parse_args()
    
    system_prompt = "You are a customer service assistant" \
                    "Help customers with their issues using available policies and tools."

    
    hooks = [] if args.no_mask else [EmailMaskingHook()]
    
    agent = Agent(
        system_prompt=system_prompt,
        tools=[get_policy],
        hooks=hooks,
        callback_handler=None,
    )
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye! Session saved.")
            break
        if not user_input:
            continue
            
        print("-" * 80)
        print("Agent: ", end="", flush=True)
        res = agent(user_input)
        print(res)
        print()
        print("-" * 80)
        print()
    agent.cleanup()


if __name__ == "__main__":
    main()
