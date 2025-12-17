# Agent loop 

The agent loop is the process by which a Strands agent processes user input, makes decisions, executes tools, and generates responses. It's designed to support complex, multi-step reasoning and actions with seamless integration of tools and language models.

At its core, the agent loop follows these steps:
1. **Receives user input** and contextual information
2. **Processes the input** using a language model (LLM)
3. **Decides** whether to use tools to gather information or perform actions
4. **Executes tools** and receives results
5. **Continues reasoning** with the new information
6. **Produces a final response** or iterates again through the loop

This cycle may repeat multiple times within a single user interaction, allowing the agent to perform complex, multi-step reasoning and autonomous behavior.

## Demo 
1. `python -m demo.01_agent_loop`
2. `I have a item bought 45 days ago. can I return it?`



# System Prompt
System prompts provide high-level instructions to the model about its role, capabilities, and constraints. 
They set the foundation for how the model should behave throughout the conversation.


# State 
Strands Agents state is maintained in several forms:

## Conversation History: 
The sequence of messages between the user and the agent. To manage conversations, you can either leverage one of Strands's provided managers or build your own manager
   1. `NullConversationManager` : do not modify the conversation history
   2. `SlidingWindowConversationManager`: implements a sliding window strategy that manages conversation history
   3. `SumarizingConversationManager`: summarizing older messages instead of simply discarding them. `summarization_agent`, `summary_ratio`, etc.

## Agent State: 
Stateful information outside of conversation context, maintained across **multiple requests**.
1. It's a key-value dictionary
2. Agent state is not passed to the model during inference but can be accessed and modified by tools and application logic.

## Request State: 
Contextual information maintained within a single request.


## Demo 
1. `python -m demo.02_state` -- NullConversationManager
2. `python -m demo.02_state --window-size 1` -- Sliding Window
3. `python -m demo.02_state --agent-state` -- agent-state is accessable across conversations
4. `python -m demo.02_state --request-state` -- request state is accessable across events within one request



# Session Management 

Persisting agent state and conversation history across multiple interactions. 
This enables agents to maintain context and continuity even when the application restarts or when deployed in distributed environments.

1. **Agent Initialization**: When an agent is created with a session manager, it automatically restores any existing state and messages from the session.
2. **Message Addition**: When a new message is added to the conversation, it's automatically persisted to the session. 
3. **Agent Invocation**: After each agent invocation, the agent state is synchronized with the session to capture any updates. 
4. **Message Redaction**: When sensitive information needs to be redacted, the session manager can replace the original message with a redacted version while maintaining conversation flow.

## Demo
1. `python -m demo.03_session --session-id 123`
2. `I have a item bought 45 days ago. can I return it? Can you connect me to an agent? My email is test@example.com if this is needed`
3.  `python -m demo.03_session --session-id 123`
4.  `what is the email address I shared with you?`
5.  





# Guardrail
Guardrails are safety mechanisms that help control AI system behavior by defining boundaries for content generation and interaction. 

https://us-east-2.console.aws.amazon.com/bedrock/home?region=us-east-2#/guardrails/email-redaction/xxuqm2u2t7sq

## Demo
1. `python -m demo.04_guardrail --session-id 123`
2. `what is the email address I shared with you?`


# Hooks
Hooks are a composable extensibility mechanism for extending agent functionality by subscribing to events throughout the agent lifecycle. 

Available hooks https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/hooks/#hook-event-lifecycle


## Demo
1. `python -m demo.05_hook`
2. `I have a item bought 45 days ago. can I return it? Can you connect me to an agent? My email is test@example.com if this is needed`
3. `what is the email address I shared with you?`


# MCP 
## Demo
1. `python -m demo.06_mcp`
2. `what are the available tools?`