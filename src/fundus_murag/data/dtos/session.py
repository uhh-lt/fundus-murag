from pydantic import BaseModel


class SessionHandle(BaseModel):
    """Response model for agent and agent sessions."""

    session_id: str
    created: int
    updated: int
    expires: int
