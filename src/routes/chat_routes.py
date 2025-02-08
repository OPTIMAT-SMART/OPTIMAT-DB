"""
Chat Routes
---------------
Handles all chat-related API endpoints.
"""

from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from typing import List
import requests
import os
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_anthropic import ChatAnthropic
from utils.responses import error_response, success_response
from utils.config import config

# Initialize the model
model_with_tools = ChatAnthropic(
    model="claude-3-haiku-20240307", 
    temperature=0, 
    api_key=config.ANTHROPIC_API_KEY
)

def find_providers(origin: str, destination: str) -> str:
    """
    Find providers that can provide services between origin and destination addresses.
    1. Name
    2. Origin Address
    3. Destination Address
    4. Equipment
    5. Health Conditions
    """
    response = requests.post(
        'https://optimat-db.onrender.com/api/v1/providers/match',
        json={
            "departureTime": "2024-03-20T09:30:00-07:00",
            "returnTime": "2024-03-20T14:45:00-07:00",
            "originAddress": origin,
            "destinationAddress": destination,
            "eligibility": ["senior", "disability"],
            "equipment": ["wheelchair"],
            "healthConditions": ["none"],
            "needsCompanion": True,
            "allowsSharing": True
        }
    )
    response_json = response.json()
    return [provider["provider_name"] for provider in response_json["data"]]

ASSISTANCE_PROMPT = """
You are a helpful assistant developed by OPTIMAT, a team that provides transportation services for people with disabilities and seniors.
You are able to find paratransit providers that can provide services between origin and destination addresses, and other criteria.

Your goal is to ask for the origin and destination addresses, and other criteria, and then find the paratransit providers that can provide services between the origin and destination addresses, and other criteria.
Please do not make up information, only use the information provided by the user.

Before sending a request to find paratransit providers, you must ask for:
1. Origin Address
2. Destination Address
3. Equipment
4. Health Conditions

Please send multiple short messages to the user to ask for the information.
If the user already provided the information, you can skip asking for it.
"""

# Initialize a dictionary to store conversations, each with their own message history
conversations = {}

# Setup LangChain tools and graph
llama_tools = model_with_tools.bind_tools([find_providers])    

def tool_calling_llm(state: MessagesState):
    return {"messages": [llama_tools.invoke(state["messages"])]}

# Build the graph
builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([find_providers]))
builder.add_conditional_edges("tool_calling_llm", tools_condition)
builder.add_edge(START, "tool_calling_llm")
builder.add_edge("tools", "tool_calling_llm")
graph = builder.compile()

def setup_chat_routes(blueprint: Blueprint) -> None:
    """Setup chat routes on the given blueprint"""
    
    @blueprint.post("/chat")
    async def chat_endpoint(request: Request) -> json:
        """
        Chat endpoint that processes a new message and returns AI responses.
        
        Request body:
        {
            "conversationId": "string",
            "newMessage": {
                "role": "human|ai|system",
                "content": "string"
            }
        }
        """
        global conversations
        
        try:
            # Extract the conversation ID and new message from the request
            conversation_id = request.json.get("conversationId")
            new_message = request.json.get("newMessage")
            
            if not conversation_id:
                return json({
                    "error": "Bad Request",
                    "details": "No conversationId provided"
                }, status=400)
            
            if not new_message:
                return json({
                    "error": "Bad Request",
                    "details": "No newMessage provided"
                }, status=400)
            
            # Initialize a new conversation if it doesn't exist
            if conversation_id not in conversations:
                # Add initial system message and a welcome message from the AI
                conversations[conversation_id] = [
                    SystemMessage(content=ASSISTANCE_PROMPT),
                    AIMessage(content="Hi! I'm here to help you find transportation services. How can I assist you today?")
                ]
            
            # Get the current conversation
            current_conversation = conversations[conversation_id]
            
            # Append the new message to the conversation based on role
            role = new_message.get("role")
            content = new_message.get("content", "")
            if role == "human":
                current_conversation.append(HumanMessage(content=content))
            elif role == "ai":
                current_conversation.append(AIMessage(content=content))
            elif role == "system":
                current_conversation.append(SystemMessage(content=content))
            else:
                return json({
                    "error": "Invalid Role",
                    "details": f"Unknown role: {role}"
                }, status=400)
            
            # Invoke the graph with the current conversation
            response_state = graph.invoke({"messages": current_conversation})
            
            # Extract new messages generated by the AI
            new_messages = response_state["messages"][len(current_conversation):]
            
            # Prepare the output to send back to the frontend
            output = []
            for msg in new_messages:
                if isinstance(msg, AIMessage):
                    output.append({"role": "ai", "content": msg.content})
                    current_conversation.append(msg)
                elif isinstance(msg, HumanMessage):
                    output.append({"role": "human", "content": msg.content})
                    current_conversation.append(msg)
                else:
                    output.append({"role": "system", "content": str(msg)})
                    current_conversation.append(msg)
        
            
            return json({"messages": output})
                
        except Exception as e:
            return json({
                "error": "Internal server error",
                "details": str(e)
            }, status=500) 
        
    @blueprint.get("/chat/health")
    async def health_check(request: Request) -> json:
        """Health check endpoint for the chat service"""
        try:
            return success_response(
                data={"status": "healthy"},
                message="Chat service is healthy"
            )
        except Exception as e:
            return error_response(
                message="Chat service health check failed",
                error_code="HEALTH_CHECK_FAILED", 
                details={"error": str(e)},
                status=500
            )