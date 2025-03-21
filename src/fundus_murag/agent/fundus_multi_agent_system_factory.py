from fundus_murag.agent.fundus_multi_agent_system import FundusMultiAgentSystem
from fundus_murag.agent.session_manager import SessionManager
from fundus_murag.data.dtos.session import SessionHandle
from fundus_murag.singleton_meta import SingletonMeta


class FundusMultiAgentSystemFactory(metaclass=SingletonMeta):
    def __init__(self):
        self.__session_manager = SessionManager[FundusMultiAgentSystem](FundusMultiAgentSystem)

    def get_or_create_agent(
        self,
        model_name: str | None = None,
        session: str | SessionHandle | None = None,
    ) -> tuple[FundusMultiAgentSystem, SessionHandle]:
        if isinstance(session, str):
            session = SessionHandle(
                session_id=session,
                created=-1,
                updated=-1,
                expires=-1,
            )

        assistant, session = self.__session_manager.get_or_create_session(
            FundusMultiAgentSystem,
            model_name=model_name,
            session=session,
        )
        return assistant, session

    def get_all_sessions(self) -> list[SessionHandle]:
        return self.__session_manager.get_all_sessions()
