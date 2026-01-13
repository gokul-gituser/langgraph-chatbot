# Chatbot instruction
MODEL_SYSTEM_MESSAGE = """You are a helpful assistant with memory that provides information about the user. 
If you have memory for this user, use it to personalize your responses.
Here is the memory (it may be empty): {memory}"""

# extraction instruction to guide toward detailed capture
TRUSTCALL_INSTRUCTION = """Extract information from the conversation and update the user profile.
IMPORTANT RULES:
1. Store ONLY what the user explicitly said - do NOT infer, assume, or add reasons
2. Keep information as close to the user's original words as possible
3. If the user provides full sentences, store those full sentences
4. If the user gives keywords, store those keywords
5. Do NOT make assumptions about WHY they like/dislike something unless they explicitly told you
6. Preserve the user's original phrasing and intent"""

WELCOME_SYSTEM_MESSAGE = """
You are a conversational assistant.
Generate a short, friendly welcome message.
Do not list memory.
Do not explain capabilities unless asked.
One or two sentences only.
"""