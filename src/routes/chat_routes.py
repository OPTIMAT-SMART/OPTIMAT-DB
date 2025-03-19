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
from langchain_aws import ChatBedrock
from utils.responses import error_response, success_response
from utils.config import config
import aiohttp
import json as json_lib

from src.utils.exceptions import ProviderMatchError
from src.services.provider_matcher import find_matching_providers
from src.utils.responses import success_response, error_response
from src.utils.validation import validate_match_request
from src.utils.db import database
from src.utils.config import config
from .provider_routes import get_provider_info_by_name, match_providers_by_criteria

# Initialize the model


# model_with_tools = ChatAnthropic(
#     model="claude-3-haiku-20240307", 
#     temperature=0, 
#     api_key=config.ANTHROPIC_API_KEY
# )
model_with_tools = ChatBedrock(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    model_kwargs=dict(temperature=0),
    aws_access_key_id=config.AWS_ACCESS_KEY,
    aws_secret_access_key=config.AWS_SECRET_KEY,
    region_name=config.AWS_REGION,
    max_tokens=1500
    # other params...
)


async def find_providers(origin: str, destination: str) -> str:
    """
    Find providers that can provide services between origin and destination addresses.
    1. Name
    2. Origin Address
    3. Destination Address
    4. Equipment
    5. Health Conditions

    After you get the trip information, summarize the entire trip information including the providers, origin, destination, equipment, and health conditions.
    """
    request = {
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
    print(f"Finding providers for {origin} to {destination}")

    matches, error = await match_providers_by_criteria(request)
    
    if error:
        print(f"Error finding providers: {str(error)}")
        return json_lib.dumps({"error": "No providers found, please try again."})
        
    provider_names = [provider["provider_name"] for provider in matches] if matches else []
    return json_lib.dumps({"providers": provider_names})

async def get_provider_info(provider_name: str) -> str:
    """
    Get accurate provider information by name.

    Args:
        provider_name (str): The name of the provider to get information about.

    Returns:
        str: The provider information.

    
    """
    print(f"Getting provider info for {provider_name}")
    return await get_provider_info_by_name(provider_name)

async def search_addresses_from_user_query(user_query: str) -> str:
    """
    Find an address or multiple addresses from a user query using Google Places API.
    If the user is asking for areas nearby them, you should ask for their address first.

    Args:
        user_query (str): The user's query containing information about what they are looking for. 

    Returns:
        str: The formatted address found from the query.
    """


    print(f"Finding address from user query: {user_query}")
    
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "X-Goog-Api-Key": config.GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.priceLevel",
        "Content-Type": "application/json"
    }
    
    body = {
        "textQuery": user_query
    }
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"Error from Google Places API: {response.status_code}")
                return ""
    except Exception as e:
        print(f"Error finding address: {str(e)}")
        return ""


ASSISTANCE_PROMPT = """
You are a helpful assistant developed by OPTIMAT, a team that provides transportation services for people with disabilities and seniors.
You are able to find paratransit providers that can provide services between origin and destination addresses, and other criteria.
You are also able to find addresses from a user query using Google Places API if the user doesn't know the exact address using the function search_addresses_from_user_query.
If the user doesn't provide an exact address, immediately use the search_addresses_from_user_query function to find the addresses.

Please do not make up information, only use the information provided by the user.

Before sending a request to find paratransit providers, you must ask for:
1. Origin Exact Address 
2. Destination Exact Address
3. Equipment
4. Health Conditions

When you get the trip information, summarize the entire trip information including the providers, origin, destination, equipment, and health conditions.
Format it concisely.

Please send multiple short messages to the user to ask for the information.
If the user already provided the information, you can skip asking for it.

If the user asks for information about a specific provider, you must ask for the provider name.
The provider name must be matched to one of the following:
        "AC Transit",
        "Arc Contra Costa (Vistability)",
        "BART",
        "Centers for Elders Independence (El Sobrante)",
        "Choice in Aging",
        "County Connections",
        "East Bay Paratransit",
        "Easy Ride Paratransit Services (El Cerrito)",
        "GoGo Concord",
        "Go San Ramon!",
        "Lamorinda Spirit",
        "LINK Paratransit",
        "Mobility Matters",
        "One-Seat Regional Ride",
        "Pleasant Hill Van Service",
        "Rossmoor Dial-A-Bus",
        "R-Transit (Richmond)",
        "R-Transit with Lyft",
        "San Pablo Senior & Disabled Transportation",
        "Senior Express Van (San Ramon)",
        "Seniors Around Town (Orinda)",
        "TDT Senior & ADA Paratransit",
        "Tri Delta Transit",
        "Walnut Creek Senior’s Club Mini-Bus",
        "WestCAT",
        "WestCAT Dial-A-Ride",
        "WestCAT Paratransit",
        "Wheels Dial-a-Ride"

    Ask for clarification if the provider name is not one of the above. Then use the provided tool to get the provider information.
    After you get the trip information, summarize the entire trip information.

    Don't format responses in markdown. Be very concise with your responses.
"""

# Initialize a dictionary to store conversations, each with their own message history
conversations = {}

# Setup LangChain tools and graph
llama_tools = model_with_tools.bind_tools([find_providers, get_provider_info, search_addresses_from_user_query])    

def tool_calling_llm(state: MessagesState):
    return {"messages": [llama_tools.invoke(state["messages"])]}

# Build the graph
builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([find_providers, get_provider_info, search_addresses_from_user_query]))
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
            response_state = await graph.ainvoke({"messages": current_conversation})
            
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