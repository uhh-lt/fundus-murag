from fastapi import APIRouter, HTTPException

from fundus_murag.assistant.assistant_factory import AssistantFactory
from fundus_murag.data.dtos.assistant import (
    AssistantModel,
    AssistantResponse,
    AssistantSession,
    MessageRequest,
)

router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
)

assistant_factory = AssistantFactory()


@router.post("/send_message", response_model=AssistantResponse)
async def send_message(request: MessageRequest):
    try:
        assistant, session = assistant_factory.get_or_create_assistant(
            model_name=request.model_name,
            session_id=request.session_id,
        )

        response_text = assistant.send_user_message(
            text_message=request.message,
        )

        return AssistantResponse(
            message=response_text,
            session=session,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=list[AssistantSession])
async def list_sessions():
    try:
        sessions = assistant_factory.get_all_sessions()
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available_models", response_model=list[AssistantModel])
async def get_available_models():
    try:
        available_models_df = assistant_factory.list_available_models()
        available_models = available_models_df.to_dict(orient="records")
        return available_models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
