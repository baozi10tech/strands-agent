"""
Main Launcher - Start all agents as A2A servers

This script launches:
1. Context Agent (Port 9000)
2. Coordinator Agent (Port 9001)
3. Negotiation Agent (Port 9002)

Each agent runs as an A2A server for inter-agent communication.
"""

import asyncio
import threading
import time
from pathlib import Path
from strands.multiagent.a2a import A2AServer

# Import agent factories
from my_assistant.agents.context_agent import create_context_agent
from my_assistant.agents.coordinator_agent import create_coordinator_agent
from my_assistant.agents.negotiation_agent import create_negotiation_agent


class AgentLauncher:
    """Launcher for all agents in the multi-agent system"""
    
    def __init__(self):
        self.servers = []
        self.threads = []
        self.base_dir = Path(__file__).parent
    
    def _run_server(self, server, name):
        """Run a server in a thread"""
        try:
            print(f"  {name} server starting...")
            server.serve()
        except Exception as e:
            print(f"  Error in {name}: {e}")
    
    def launch_context_agent(self):
        """Launch Context Agent on port 9000"""
        print("\n[1/3] Launching Context Agent (Port 9000)...")
        
        # Create agent
        agent = create_context_agent(
            session_id="context-agent-session",
            storage_dir="./my_assistant_sessions"
        )
        
        # Create A2A server
        server = A2AServer(agent=agent, port=9000)
        self.servers.append(("Context Agent", server))
        
        # Start server in thread
        thread = threading.Thread(
            target=self._run_server,
            args=(server, "Context Agent"),
            daemon=True
        )
        thread.start()
        self.threads.append(thread)
        
        print("  ✓ Context Agent started on port 9000")
    
    def launch_negotiation_agent(self):
        """Launch Negotiation Agent on port 9002"""
        print("\n[2/3] Launching Negotiation Agent (Port 9002)...")
        
        # Create agent
        agent = create_negotiation_agent(
            session_id="negotiation-agent-session",
            storage_dir="./my_assistant_sessions"
        )
        
        # Create A2A server
        server = A2AServer(agent=agent, port=9002)
        self.servers.append(("Negotiation Agent", server))
        
        # Start server in thread
        thread = threading.Thread(
            target=self._run_server,
            args=(server, "Negotiation Agent"),
            daemon=True
        )
        thread.start()
        self.threads.append(thread)
        
        print("  ✓ Negotiation Agent started on port 9002")
    
    def launch_coordinator_agent(self):
        """Launch Coordinator Agent on port 9001"""
        print("\n[3/3] Launching Coordinator Agent (Port 9001)...")
        
        # Create agent
        agent = create_coordinator_agent(
            session_id="coordinator-agent-session",
            storage_dir="./my_assistant_sessions"
        )
        
        # Create A2A server
        server = A2AServer(agent=agent, port=9001)
        self.servers.append(("Coordinator Agent", server))
        
        # Start server in thread
        thread = threading.Thread(
            target=self._run_server,
            args=(server, "Coordinator Agent"),
            daemon=True
        )
        thread.start()
        self.threads.append(thread)
        
        print("  ✓ Coordinator Agent started on port 9001")
    
    def print_status(self):
        """Print status of all agents"""
        print("\n" + "="*70)
        print("  MULTI-AGENT SYSTEM STATUS")
        print("="*70)
        
        for name, server in self.servers:
            status = "Running"
            print(f"  {name}: {status}")
        
        print("="*70)
    
    def print_usage_instructions(self):
        """Print usage instructions"""
        print("\n" + "="*70)
        print("  SYSTEM READY - USAGE INSTRUCTIONS")
        print("="*70)
        print("""
The multi-agent customer service system is now running!

To interact with the system, open TWO separate terminal windows:

Terminal 1 - CS Simulator (Human acts as Amazon CS):
  $ cd my_assistant
  $ python -m cli.cs_simulator_cli

Terminal 2 - Customer CLI (Submit customer issues):
  $ cd my_assistant
  $ python -m cli.customer_cli

Example workflow:
1. Start Customer CLI and describe an issue
2. The system will analyze and delegate to Negotiation Agent
3. Negotiation Agent will contact CS (CS Simulator)
4. Human in CS Simulator responds as Amazon CS would
5. Negotiation continues until resolved

To stop the system:
  Press Ctrl+C in this window

For more information, see: my_assistant/USAGE_GUIDE.md
        """)
        print("="*70 + "\n")
    
    async def monitor_agents(self):
        """Monitor agent threads"""
        try:
            while True:
                # Check if any thread has died
                for i, thread in enumerate(self.threads):
                    if not thread.is_alive():
                        name = self.servers[i][0]
                        print(f"\n⚠️  Warning: {name} thread has stopped unexpectedly!")
                
                # Sleep for a bit
                await asyncio.sleep(5)
        
        except KeyboardInterrupt:
            print("\n\nShutting down agents...")
            self.cleanup()
    
    def cleanup(self):
        """Clean up all servers"""
        print("\nStopping all agents...")
        
        for name, server in self.servers:
            print(f"  Stopping {name}...")
            # Servers will be stopped when main thread exits
        
        print("\n✓ All agents stopped. Goodbye!\n")
    
    async def run(self):
        """Main run method"""
        print("\n" + "="*70)
        print("  MULTI-AGENT CUSTOMER SERVICE SYSTEM LAUNCHER")
        print("="*70)
        
        try:
            # Launch agents in order
            self.launch_context_agent()
            time.sleep(2)  # Wait for Context Agent to start
            
            self.launch_negotiation_agent()
            time.sleep(2)  # Wait for Negotiation Agent to start
            
            self.launch_coordinator_agent()
            time.sleep(2)  # Wait for Coordinator Agent to start
            
            # Print status
            self.print_status()
            self.print_usage_instructions()
            
            # Monitor agents
            await self.monitor_agents()
        
        except Exception as e:
            print(f"\nError: {e}")
            self.cleanup()


async def main():
    """Main entry point"""
    launcher = AgentLauncher()
    await launcher.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n")
