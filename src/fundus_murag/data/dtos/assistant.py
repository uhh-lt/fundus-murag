from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    """Request model for sending a text message to an assistant."""

    message: str = Field(..., description="The text message to send to the assistant.")
    base64_images: list[str] | None = Field(
        None,
        description="Base64 encoded images that gets appended to the text message.",
    )
    model_name: str = Field(
        "google/gemini-2.0-flash",
        description="The name of the model to use for the assistant. The model must be available in the system.",
    )
    session_id: str | None = Field(
        None,
        description="The session ID to use for the assistant. If None, a new session is created.",
    )


class AssistantResponse(BaseModel):
    """Response model for assistant interactions."""

    message: str
    session_id: str
    model_name: str


class AssistantModel(BaseModel):
    """Response model for available assistant models."""

    name: str
    display_name: str


class AssistantSession(BaseModel):
    """Response model for assistant sessions."""

    session_id: str
    model_name: str
    created: int


class ChatMessage(BaseModel):
    """Model for chat messages to be displayed in the frontend."""

    role: str
    content: str
