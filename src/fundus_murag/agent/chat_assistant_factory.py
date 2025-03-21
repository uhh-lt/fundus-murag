from fundus_murag.agent.chat_assistant import ChatAssistant
from fundus_murag.agent.session_manager import SessionManager
from fundus_murag.agent.tools.tools import Tool
from fundus_murag.data.dtos.session import SessionHandle
from fundus_murag.singleton_meta import SingletonMeta


class ChatAssistantFactory(metaclass=SingletonMeta):
    def __init__(self):
        self.__session_manager = SessionManager[ChatAssistant](ChatAssistant)

    def get_or_create_assistant(
        self,
        assistant_name: str | None = None,
        model_name: str | None = None,
        system_instruction: str | None = None,
        available_tools: list[Tool] | None = None,
        session: str | SessionHandle | None = None,
    ) -> tuple[ChatAssistant, SessionHandle]:
        if isinstance(session, str):
            session = SessionHandle(
                session_id=session,
                created=-1,
                updated=-1,
                expires=-1,
            )

        assistant, session = self.__session_manager.get_or_create_session(
            ChatAssistant,
            assistant_name=assistant_name,
            model_name=model_name,
            system_instruction=system_instruction,
            available_tools=available_tools,
            session=session,
        )
        return assistant, session

    def get_all_sessions(self) -> list[SessionHandle]:
        return self.__session_manager.get_all_sessions()
