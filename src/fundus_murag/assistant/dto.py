from dataclasses import dataclass


# we need to use dataclasses here because we want to store it in a
# MESOP state which does not support pydantic models
@dataclass(kw_only=True)
class ChatMessage:
    role: str
    content: str
