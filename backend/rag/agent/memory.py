SESSION_MEMORY = {}

def get_formatted_history(session_id: str, limit: int = 4) -> str:
    """Returns the last N turns of conversation for the given session_id."""
    history = SESSION_MEMORY.get(session_id, [])
    if not history:
        return ""
    
    recent_history = history[-limit:]
    formatted = "--- Previous Conversation Context ---\n"
    for turn in recent_history:
        formatted += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"
    formatted += "--------------------------------------\n"
    return formatted

def add_to_history(session_id: str, user_msg: str, assistant_msg: str):
    """Adds a new conversation turn to the session memory."""
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = []
    SESSION_MEMORY[session_id].append({
        "user": user_msg, 
        "assistant": assistant_msg
    })
