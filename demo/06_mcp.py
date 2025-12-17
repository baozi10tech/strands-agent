#!/usr/bin/env python3
import argparse
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters


system_prompt = """You are a helpful AWS assistant with access to AWS documentation.
Help users understand AWS services and best practices."""


def main():
    # Create MCP client
    mcp_client = MCPClient(lambda: stdio_client(StdioServerParameters(
        command="builder-mcp", 
        args=[])))

    # Manual lifecycle management
    with mcp_client:
        # Get the tools from the MCP server
        tools = mcp_client.list_tools_sync()

        # Create an agent with these tools
        agent = Agent(tools=tools)
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
