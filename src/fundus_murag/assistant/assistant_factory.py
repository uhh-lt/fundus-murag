import pandas as pd

from fundus_murag.assistant.chat_assistant import ChatAssistant
from fundus_murag.assistant.session_manager import SessionManager
from fundus_murag.assistant.tools.tools import Tool
from fundus_murag.data.dtos.assistant import AssistantModel, SessionHandle
from fundus_murag.singleton_meta import SingletonMeta


class AssistantFactory(metaclass=SingletonMeta):
    def __init__(self):
        self.__session_manager = SessionManager[ChatAssistant]()

    def get_or_create_assistant(
        self,
        model_name: str | None = None,
        system_instruction: str | None = None,
        available_tools: list[Tool] | None = None,
        session_id: str | None = None,
    ) -> tuple[ChatAssistant, SessionHandle]:
        assistant, session = self.__session_manager.get_or_create_session(
            ChatAssistant,
            model_name=model_name,
            system_instruction=system_instruction,
            available_tools=available_tools,
            session_id=session_id,
        )
        return assistant, session

    def get_all_sessions(self) -> list[SessionHandle]:
        return self.__session_manager.get_all_sessions()

    def list_available_models(self) -> pd.DataFrame:
        models = ChatAssistant.list_available_models()
        return models

    def get_default_model(self) -> AssistantModel:
        default = ChatAssistant.get_default_model()
        return default
