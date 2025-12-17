"""
Customer CLI - Interface for customers to submit service issues

This CLI allows customers to:
1. Submit service issues to the Coordinator Agent
2. Provide order and customer information
3. Track the status of their issue
4. Receive resolution updates
"""

import asyncio
import sys
from pathlib import Path
import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class CustomerCLI:
    """CLI for customers to interact with the customer service system"""
    
    def __init__(self, coordinator_url: str = "http://localhost:9001"):
        self.coordinator_url = coordinator_url
        self.client = None
        self.running = False
    
    def print_header(self):
        """Print CLI header"""
        print("\n" + "="*70)
        print("  AMAZON CUSTOMER SERVICE - AI ASSISTANT")
        print("="*70)
        print("\nWelcome! I'm here to help you with your Amazon orders and issues.")
        print("\nCommands:")
        print("  /status  - Check status of your current issue")
        print("  /help    - Show this help message")
        print("  /quit    - Exit the customer service system")
        print("="*70 + "\n")
    
    def print_separator(self):
        """Print separator line"""
        print("-" * 70)
    
    async def send_to_coordinator(self, message: str) -> str:
        """
        Send a message to the Coordinator Agent via A2A.
        
        Args:
            message: Customer message
        
        Returns:
            Response from Coordinator Agent
        """
        try:
            async with httpx.AsyncClient(timeout=300) as httpx_client:
                # Get agent card from Coordinator Agent
                resolver = A2ACardResolver(httpx_client=httpx_client, base_url=self.coordinator_url)
                agent_card = await resolver.get_agent_card()
                
                # Create A2A client
                config = ClientConfig(httpx_client=httpx_client, streaming=False)
                factory = ClientFactory(config)
                client = factory.create(agent_card)
                
                # Create and send message
                a2a_message = Message(
                    kind="message",
                    role=Role.user,
                    parts=[Part(TextPart(kind="text", text=message))]
                )
                
                # Collect response
                response_text = ""
                async for event in client.send_message(a2a_message):
                    if hasattr(event, 'text'):
                        response_text += event.text
                    elif hasattr(event, 'content'):
                        response_text += str(event.content)
                
                return response_text if response_text else "No response from Coordinator Agent"
        
        except Exception as e:
            return f"Error communicating with customer service: {str(e)}\nPlease make sure the system is running."
    
    def show_help(self):
        """Show help information"""
        print("\n" + "="*70)
        print("  HELP - HOW TO USE THIS SYSTEM")
        print("="*70)
        print("""
This AI-powered customer service system can help you with:
- Damaged or defective items
- Late or delayed deliveries
- Wrong items received
- Returns and refunds
- Missing packages

How to report an issue:
1. Describe your problem in your own words
2. Mention your order ID if you have it (format: 123-4567890-1234567)
3. The system will analyze your issue and handle the negotiation

Example issues you can report:
- "My laptop arrived damaged. Order 123-4567890-1234567"
- "My package is 5 days late and still hasn't arrived"
- "I received the wrong item - ordered AirPods but got a phone case"
- "I want to return an item I bought 20 days ago"

The system will:
1. Analyze your issue
2. Retrieve relevant policies
3. Negotiate with Customer Service on your behalf
4. Keep you updated on progress
        """)
        print("="*70 + "\n")
    
    async def run(self):
        """Main CLI loop"""
        self.running = True
        self.print_header()
        
        print("👋 Hello! How can I help you today?\n")
        print("(Describe your issue, or type /help for examples)\n")
        
        try:
            while self.running:
                # Get customer input
                print("You: ", end='', flush=True)
                user_input = input().strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() == '/quit':
                    print("\nThank you for using Amazon Customer Service. Goodbye!")
                    self.running = False
                    break
                
                if user_input.lower() == '/help':
                    self.show_help()
                    continue
                
                if user_input.lower() == '/status':
                    print("\n⏳ Checking status...\n")
                    status_msg = "Please provide a status update on my current issue."
                    response = await self.send_to_coordinator(status_msg)
                    print(f"System: {response}\n")
                    continue
                
                # Send message to Coordinator Agent
                print("\n⏳ Processing your request...\n")
                self.print_separator()
                
                response = await self.send_to_coordinator(user_input)
                
                print(f"\n🤖 AI Assistant: {response}\n")
                self.print_separator()
                print()
        
        except KeyboardInterrupt:
            print("\n\nThank you for using Amazon Customer Service. Goodbye!")
        except Exception as e:
            print(f"\n\nError: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup when exiting"""
        print()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Customer Service CLI")
    parser.add_argument(
        "--coordinator-url",
        default="http://localhost:9001",
        help="URL of the Coordinator Agent (default: http://localhost:9001)"
    )
    
    args = parser.parse_args()
    
    cli = CustomerCLI(coordinator_url=args.coordinator_url)
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
