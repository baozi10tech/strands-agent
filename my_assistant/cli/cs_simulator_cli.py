"""
CS Simulator CLI - Manual interface for human tester to act as Amazon Customer Service

This CLI allows a human to:
1. Wait for messages from the Negotiation Agent
2. Type responses as Amazon CS would
3. Send responses back to the Negotiation Agent
4. View conversation history
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from my_assistant.utils.message_queue import get_global_queue


class CSSimulatorCLI:
    """CLI for human to simulate Amazon Customer Service"""
    
    def __init__(self):
        self.queue = get_global_queue()
        self.running = False
    
    def print_header(self):
        """Print CLI header"""
        print("\n" + "="*70)
        print("  AMAZON CUSTOMER SERVICE SIMULATOR")
        print("="*70)
        print("\nYou are now acting as an Amazon Customer Service representative.")
        print("Wait for customer messages and respond appropriately.")
        print("\nCommands:")
        print("  /history  - Show conversation history")
        print("  /quit     - Exit the simulator")
        print("="*70 + "\n")
    
    def print_separator(self):
        """Print separator line"""
        print("-" * 70)
    
    def display_history(self):
        """Display conversation history"""
        history = self.queue.get_conversation_history()
        
        if not history:
            print("\n[No conversation history yet]\n")
            return
        
        print("\n" + "="*70)
        print("  CONVERSATION HISTORY")
        print("="*70)
        
        for i, entry in enumerate(history, 1):
            role = entry['role'].upper()
            message = entry['message']
            timestamp = entry['timestamp']
            
            print(f"\n[{i}] {role} - {timestamp}")
            print(f"    {message}")
        
        print("\n" + "="*70 + "\n")
    
    async def wait_for_customer_message(self):
        """Wait for a message from the Negotiation Agent (acting as customer)"""
        try:
            message = await self.queue.wait_for_agent_message(timeout=300.0)  # 5 min timeout
            return message
        except asyncio.TimeoutError:
            return None
    
    def send_cs_response(self, response: str):
        """Send CS response back to the Negotiation Agent"""
        self.queue.send_from_cs(response)
    
    async def run(self):
        """Main CLI loop"""
        self.running = True
        self.print_header()
        
        print("[CS Simulator Ready] Waiting for customer to initiate contact...\n")
        
        try:
            while self.running:
                # Wait for customer message
                customer_message = await self.wait_for_customer_message()
                
                if customer_message is None:
                    print("\n[Timeout] No customer message received. Still waiting...")
                    continue
                
                # Display customer message
                self.print_separator()
                print(f"\n🗣️  CUSTOMER: {customer_message}\n")
                self.print_separator()
                
                # Get CS response from human
                while True:
                    print("\n💼 YOU (Amazon CS): ", end='', flush=True)
                    cs_response = input().strip()
                    
                    # Handle commands
                    if cs_response.lower() == '/quit':
                        print("\n[Exiting CS Simulator...]")
                        self.running = False
                        break
                    
                    if cs_response.lower() == '/history':
                        self.display_history()
                        continue
                    
                    # Validate response
                    if not cs_response:
                        print("  ⚠️  Please enter a response or use /quit to exit")
                        continue
                    
                    # Send response to Negotiation Agent
                    self.send_cs_response(cs_response)
                    print("  ✓ Response sent to customer")
                    break
                
                if not self.running:
                    break
                
                print("\n[Waiting for next customer message...]\n")
        
        except KeyboardInterrupt:
            print("\n\n[KeyboardInterrupt] Exiting CS Simulator...")
        except Exception as e:
            print(f"\n\n[Error] {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup when exiting"""
        print("\nCS Simulator session ended.")
        print("Conversation history preserved in message queue.\n")


async def main():
    """Main entry point"""
    simulator = CSSimulatorCLI()
    await simulator.run()


if __name__ == "__main__":
    asyncio.run(main())
