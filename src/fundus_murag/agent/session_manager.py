import time
import uuid
from typing import Generic, TypeVar

from loguru import logger

from fundus_murag.data.dtos.session import SessionHandle

T = TypeVar("T")

MAX_SESSION_AGE = 60 * 60  # 1 hour
MAX_SESSIONS = 100


class SessionManager(Generic[T]):
    def __init__(self, clazz: type[T]):
        self.__session_objects: dict[str, T] = {}
        self.__sessions: dict[str, SessionHandle] = {}
        self.__old_sesssions: dict[str, SessionHandle] = {}
        # unfortunately, Python does not have a built-in way to get the class name of a generic type at runtime
        # so we have to pass the class name explicitly
        self._concrete_class_name = clazz.__name__
        logger.info(f"Initialized Session Manager for {self._concrete_class_name}")

    def __delete_session(self, session_id: str) -> bool:
        if session_id in self.__sessions:
            session = self.__sessions[session_id]
            self.__old_sesssions[session_id] = session.model_copy()
            del self.__sessions[session_id]
            del self.__session_objects[session_id]
            logger.debug(f"Deleted {self._concrete_class_name} Session {session_id}")
            return True
        return False

    def get_all_sessions(self) -> list[SessionHandle]:
        sessions = []
        for session in self.__sessions.values():
            sessions.append(session.model_copy())
        return sessions

    def __create_session(
        self,
        cls: type[T],
        *args,
        **kwargs,
    ) -> tuple[T, SessionHandle]:
        logger.info(f"Creating new {self._concrete_class_name} Session")
        obj = cls(*args, **kwargs)
        session_id = str(uuid.uuid4())
        now = int(time.time())
        session = SessionHandle(
            session_id=session_id,
            created=now,
            updated=now,
            expires=now + MAX_SESSION_AGE,
        )
        self.__session_objects[session_id] = obj
        self.__sessions[session_id] = session
        logger.debug(f"Created new {self._concrete_class_name} Session {session_id}")
        return obj, session

    def __get_session(self, session_id: str) -> SessionHandle:
        if session_id in self.__sessions:
            session = self.__sessions[session_id]
            logger.debug(f"Reusing existing {self._concrete_class_name} for session {session.session_id}")
            session.updated = int(time.time())
            session.expires = session.updated + MAX_SESSION_AGE
            self.__sessions[session_id] = session
            return session
        elif session_id in self.__old_sesssions:
            logger.error(f"Session {session_id} has expired!")
            raise KeyError(f"Session {session_id} has expired!")
        else:
            logger.error(f"Session {session_id} not found!")
            raise KeyError(f"Session {session_id} not found!")

    def get_or_create_session(
        self,
        cls: type[T],
        session: SessionHandle | None = None,
        *args,
        **kwargs,
    ) -> tuple[T, SessionHandle]:
        self.__clean_up_sessions()

        if session is not None and session.session_id != "":
            session = self.__get_session(session.session_id)
            obj = self.__session_objects[session.session_id]
        else:
            obj, session = self.__create_session(cls, *args, **kwargs)

        return obj, session

    def __clean_up_sessions(self) -> None:
        current_time = int(time.time())
        session_ids = list(self.__sessions.keys())
        for session_id in session_ids:
            session = self.__sessions[session_id]
            if current_time > session.expires:
                self.__delete_session(session_id)

        if len(self.__sessions) > MAX_SESSIONS:
            # delete oldest sessions
            sorted_sessions = sorted(self.__sessions.items(), key=lambda x: x[1].created)
            for session_id, _ in sorted_sessions[: len(self.__sessions) - MAX_SESSIONS]:
                self.__delete_session(session_id)
