
import os
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.redis import RedisSaver
from langgraph.store.redis import RedisStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.base import BaseStore
from trustcall import create_extractor
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .models import UserProfile
from .prompts import MODEL_SYSTEM_MESSAGE, TRUSTCALL_INSTRUCTION, WELCOME_SYSTEM_MESSAGE


load_dotenv()


model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7
)


# Create the extractor
trustcall_extractor = create_extractor(
    model,
    tools=[UserProfile],
    tool_choice="UserProfile",
)

def router_node(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
    return {}


def route_decision(state: MessagesState, config: RunnableConfig) -> Literal["welcome", "conversation"]:
    intent = config["configurable"].get("intent")
    if intent == "start":
        return "welcome"
    return "conversation"



def welcome_node(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
    response = model.invoke(
        [SystemMessage(content=WELCOME_SYSTEM_MESSAGE)]
    )
    return {"messages": response}


def conversation(state: MessagesState, config: RunnableConfig,*, store: BaseStore):

    """Load memory from the store and use it to personalize the chatbot's response."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve memory from the store
    namespace = ("memory", user_id)
    existing_memory = store.get(namespace, "user_memory")

    # Format the memories for the system prompt
    if existing_memory and existing_memory.value:
        memory_dict = existing_memory.value
        formatted_memory = (
            f"Name: {memory_dict.get('user_name', 'Unknown')}\n"
            f"Age: {memory_dict.get('age', 'Not provided')}\n"
            f"Location: {memory_dict.get('location', 'Not provided')}\n"
            f"Interests: {', '.join(memory_dict.get('interests', []))}\n"
            f"Dislikes: {', '.join(memory_dict.get('dislikes', []))}\n"
            f"Notes: {memory_dict.get('additional_notes', 'None')}"
        )
        
    else:
        formatted_memory = None

    # Format the memory in the system prompt
    system_msg = MODEL_SYSTEM_MESSAGE.format(memory=formatted_memory)

    # Respond using memory as well as the chat history
    response = model.invoke([SystemMessage(content=system_msg)]+state["messages"])

    return {"messages": response}

def write_memory(state: MessagesState, config: RunnableConfig,*, store: BaseStore):

    """Reflect on the chat history and save a memory to the store."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve existing memory from the store
    namespace = ("memory", user_id)
    existing_memory = store.get(namespace, "user_memory")
        
    # Get the profile as the value from the list, and convert it to a JSON doc
    existing_profile = {"UserProfile": existing_memory.value} if existing_memory else None
    
    # Invoke the extractor
    result = trustcall_extractor.invoke({"messages": [SystemMessage(content=TRUSTCALL_INSTRUCTION)]+state["messages"], "existing": existing_profile})
    
    # Get the updated profile as a JSON object
    updated_profile = result["responses"][0].model_dump()

    # Save the updated profile
    key = "user_memory"
    store.put(namespace, key, updated_profile)


def _build_graph():
    """Build and compile the LangGraph state graph"""
    builder = StateGraph(MessagesState)

    # Add nodes
    builder.add_node("router", router_node)
    builder.add_node("welcome", welcome_node)
    builder.add_node("conversation", conversation)
    builder.add_node("write_memory", write_memory)

    # Add edges
    builder.add_edge(START, "router")
    
    builder.add_conditional_edges(
        "router",
        route_decision,
        {
            "welcome": "welcome",
            "conversation": "conversation",
        },
    )

    builder.add_edge("welcome", END)
    builder.add_edge("conversation", "write_memory")
    builder.add_edge("write_memory", END)

    # Store for long-term (across-thread) memory
    REDIS_URI = os.getenv("REDIS_URL")
    with RedisSaver.from_conn_string(REDIS_URI) as checkpointer:
        checkpointer.setup()

        with RedisStore.from_conn_string(REDIS_URI) as store:
            store.setup()

            graph = builder.compile(
                checkpointer=checkpointer,
                store=store,
            )
    return graph


_graph = None


def _get_graph():
    """Get or initialize the compiled graph (singleton pattern)"""
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


       


async def run_langgraph(user_id: str, text: str,intent: str | None = None) -> str:
    """
    Runs one LangGraph turn and returns the AI response text.
    """
    graph = _get_graph()
    thread_id = f"tg-{user_id}"

    config = {
        "configurable": {
            "user_id": user_id,
            "thread_id": thread_id,
            "intent": intent,
        }
    }

    final_ai_message = None

    for chunk in graph.stream(
        {"messages": [HumanMessage(content=text)]},
        config,
        stream_mode="values",
    ):
        last_msg = chunk["messages"][-1]
        if isinstance(last_msg, AIMessage):
            final_ai_message = last_msg

    return final_ai_message.content if final_ai_message else "No response"