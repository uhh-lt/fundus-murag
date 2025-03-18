import time
import uuid

import pandas as pd
from loguru import logger

from fundus_murag.assistant.fundus_assistant import FundusAssistant
from fundus_murag.assistant.tools.tools import FundusTool
from fundus_murag.data.dtos.assistant import AssistantModel, AssistantSession
from fundus_murag.singleton_meta import SingletonMeta

MAX_SESSION_AGE = 60 * 60  # 1 hour
MAX_SESSIONS = 100


class AssistantFactory(metaclass=SingletonMeta):
    def __init__(self):
        self.__sessions: dict[str, FundusAssistant] = {}
        self.__session_timestamps: dict[str, float] = {}
        self.__old_sesssions: set[str] = set()

    def get_or_create_assistant(
        self,
        model_name: str | None = None,
        system_instruction: str | None = None,
        session_id: str | None = None,
    ) -> tuple[FundusAssistant, AssistantSession]:
        self.__delete_old_sessions()

        if session_id is not None and session_id != "":
            if session_id in self.__sessions:
                logger.debug(f"Reusing existing assistant for session {session_id}")
                assistant = self.__sessions[session_id]
            elif session_id in self.__old_sesssions:
                logger.error(f"Session {session_id} has expired!")
                raise KeyError(f"Session {session_id} has expired!")
            else:
                logger.error(f"Session {session_id} not found!")
                raise KeyError(f"Session {session_id} not found!")
        else:
            assistant, session_id = self.__create_session(
                model_name=model_name, system_instruction=system_instruction
            )
            self.__sessions[session_id] = assistant

        session = AssistantSession(
            session_id=session_id,
            model_name=assistant.model_name,
            created=int(self.__session_timestamps[session_id]),
        )

        return assistant, session

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.__sessions:
            del self.__sessions[session_id]
            return True
        return False

    def get_all_sessions(self) -> list[AssistantSession]:
        sessions = []
        for session_id, assistant in self.__sessions.items():
            sessions.append(
                AssistantSession(
                    session_id=session_id,
                    model_name=assistant.model_name,
                    created=int(self.__session_timestamps[session_id]),
                )
            )
        return sessions

    def list_available_models(self) -> pd.DataFrame:
        models = FundusAssistant.list_available_models()
        return models

    def get_default_model(self) -> AssistantModel:
        default = FundusAssistant.get_default_model()
        return default

    def __create_session(
        self,
        model_name: str | None = None,
        system_instruction: str | None = None,
        available_tools: list[FundusTool] | None = None,
    ) -> tuple[FundusAssistant, str]:
        logger.info(f"Creating new assistant for model {model_name}")
        assistant = FundusAssistant(
            model_name=model_name,
            system_instruction=system_instruction,
            available_tools=available_tools,
        )
        session_id = str(uuid.uuid4())
        self.__session_timestamps[session_id] = time.time()
        return assistant, session_id

    def __delete_old_sessions(self) -> None:
        current_time = time.time()
        for session_id, timestamp in self.__session_timestamps.items():
            if current_time - timestamp > MAX_SESSION_AGE:
                logger.info(f"Deleting session {session_id} due to inactivity")
                del self.__sessions[session_id]
                del self.__session_timestamps[session_id]
                self.__old_sesssions.add(session_id)

        if len(self.__sessions) > MAX_SESSIONS:
            # remove oldest sessions
            sorted_sessions = sorted(
                self.__session_timestamps.items(), key=lambda x: x[1]
            )
            for session_id, _ in sorted_sessions[: len(self.__sessions) - MAX_SESSIONS]:
                logger.info(f"Deleting session {session_id} due to session limit")
                del self.__sessions[session_id]
                del self.__session_timestamps[session_id]
                self.__old_sesssions.add(session_id)
