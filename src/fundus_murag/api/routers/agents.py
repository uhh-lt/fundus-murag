from fastapi import APIRouter, HTTPException

from fundus_murag.agent.chat_assistant import ChatAssistant
from fundus_murag.agent.fundus_multi_agent_system_factory import FundusMultiAgentSystemFactory
from fundus_murag.data.dtos.agent import AgentModel, AgentResponse, MessageRequest, SessionHandle

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
)

fundus_agent_factory = FundusMultiAgentSystemFactory()


@router.post("/send_message", response_model=AgentResponse)
async def send_message(request: MessageRequest):
    try:
        agent, session = fundus_agent_factory.get_or_create_agent(
            model_name=request.model_name,
            session=request.session_id,
        )

        response_text = agent.handle_user_request(
            user_request=request.message,
            base64_image=request.user_image_id,
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
        sessions = fundus_agent_factory.get_all_sessions()
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
