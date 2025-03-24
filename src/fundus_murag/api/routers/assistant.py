from fastapi import APIRouter, HTTPException

from fundus_murag.agent.chat_assistant import ChatAssistant
from fundus_murag.agent.chat_assistant_factory import ChatAssistantFactory
from fundus_murag.agent.prompts.single_assistant import SINGLE_ASSISTANT_SYSTEM_INSTRUCTION
from fundus_murag.agent.tools.tools import (
    get_image_analysis_tool,
    get_lex_search_tool,
    get_lookup_tool,
    get_sim_search_tool,
)
from fundus_murag.data.dtos.agent import AgentModel, AgentResponse, MessageRequest, SessionHandle

router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
)

assistant_factory = ChatAssistantFactory()


@router.post("/send_message", response_model=AgentResponse)
async def send_message(request: MessageRequest):
    try:
        assistant, session = assistant_factory.get_or_create_assistant(
            assistant_name="FUNdus! Assistant",
            system_instruction=SINGLE_ASSISTANT_SYSTEM_INSTRUCTION,
            available_tools=[
                get_sim_search_tool(),
                get_lex_search_tool(),
                get_lookup_tool(),
                get_image_analysis_tool(),
            ],
            model_name=request.model_name,
            session=request.session_id,
        )

        # hacky way to handle the case where the user wants to find similar images to the one they provided.
        # We alter the prompt here because we want to display the original message in the frontend ...
        if (
            request.message == "Find FundusRecords with similar images to this one"
            and request.user_image_id is not None
        ):
            request.message = (
                "Find FundusRecords with images similar to the user provided image "
                f"with the following ID: `user_image_id={request.user_image_id}`"
            )

        response_text = assistant.send_user_message(
            text_message=request.message,
        )

        return AgentResponse(
            message=response_text,
            session=session,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=list[SessionHandle])
async def list_sessions():
    try:
        sessions = assistant_factory.get_all_sessions()
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available_models", response_model=list[AgentModel])
async def get_available_models():
    try:
        available_models_df = ChatAssistant.list_available_models()
        available_models = available_models_df.to_dict(orient="records")
        return available_models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
