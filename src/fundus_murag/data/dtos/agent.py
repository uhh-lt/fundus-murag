from pydantic import BaseModel, Field

from fundus_murag.data.dtos.session import SessionHandle


class MessageRequest(BaseModel):
    """Request model for sending a text message to a FUNDus Agent."""

    message: str = Field(..., description="The text message to send to the FUNDus Agent.")
    base64_image: str | None = Field(
        None,
        description="A Base64 encoded image that gets appended to the text message.",
    )
    model_name: str | None = Field(
        "google/gemini-2.0-flash",
        description="The name of the model to use for the FUNDus Agent. The model must be available in the system. If a session ID is provided, this field is ignored.",
    )
    session_id: str | None = Field(
        None,
        description="The session ID to use for the FUNDus Agent. If None, a new session is created.",
    )


class AgentModel(BaseModel):
    """Response model for available FUNDus Agent models."""

    name: str
    display_name: str


class AgentResponse(BaseModel):
    """Response model for FUNDus Agent interactions."""

    message: str
    session: SessionHandle


class ChatMessage(BaseModel):
    """Model for chat messages to be returned to the client."""

    role: str
    content: str
