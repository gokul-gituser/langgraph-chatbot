"""
LangGraph Chatbot Module

A reusable module for building chatbots with LangGraph that includes:
- User profile memory management
- Redis-based persistence
- Welcome message handling
- Conversation management
"""

from .core import run_langgraph

__version__ = "1.0.0"
__author__ = "gokul"
__all__ = ["run_langgraph"]