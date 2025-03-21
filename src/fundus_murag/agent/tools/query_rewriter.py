from enum import Enum

from loguru import logger

from fundus_murag.agent.chat_assistant import ChatAssistant
from fundus_murag.agent.chat_assistant_factory import ChatAssistantFactory
from fundus_murag.agent.prompts.query_rewriting import (
    QUERY_REWRITER_TEXT_IMAGE_SYSTEM_INSTRUCTION,
    QUERY_REWRITER_TEXT_TEXT_SYSTEM_INSTRUCTION,
)
from fundus_murag.singleton_meta import SingletonMeta


class QueryRewritingTask(str, Enum):
    T2T = "t2t"
    T2I = "t2i"


class QueryRewriter(metaclass=SingletonMeta):
    def __init__(self):
        self._factory = ChatAssistantFactory()

    def _get_query_rewriter_assistant(self, task: QueryRewritingTask) -> ChatAssistant:
        match task:
            case QueryRewritingTask.T2T:
                system_instruction = QUERY_REWRITER_TEXT_TEXT_SYSTEM_INSTRUCTION
            case QueryRewritingTask.T2I:
                system_instruction = QUERY_REWRITER_TEXT_IMAGE_SYSTEM_INSTRUCTION
            case _:
                raise ValueError(f"Unsupported task type: {task}")

        assistant, _ = self._factory.get_or_create_assistant(
            assistant_name="Query Rewriter",
            model_name=None,
            system_instruction=system_instruction,
            available_tools=None,  # No tools!
            session=None,  # Start a new session
        )
        return assistant

    def rewrite_user_query_for_cross_modal_text_to_image_search(self, user_query: str) -> str:
        """
        Rewrites a user query to enhance the results of a cross-modal text-image search.

        Args:
            user_query: The user query to rewrite.

        Returns:
            The rewritten user query optimized for cross-modal text-image search.
        """
        try:
            assistant = self._get_query_rewriter_assistant(QueryRewritingTask.T2I)
            rewritten_query = assistant.send_user_message(user_query)
        except Exception as e:
            logger.error(f"Error rewriting user query for text-to-image search: {e}")
            rewritten_query = user_query

        logger.debug(f"User Query: {user_query}")
        logger.debug(f"Rewritten Query: {rewritten_query}")

        return rewritten_query

    def rewrite_user_query_for_text_to_text_search(self, user_query: str) -> str:
        """
        Rewrites a user query to enhance the results of a semantic textual similarity search.

        Args:
            user_query: The user query to rewrite.

        Returns:
            The rewritten user query optimized for semantic textual similarity search.
        """

        try:
            assistant = self._get_query_rewriter_assistant(QueryRewritingTask.T2T)
            rewritten_query = assistant.send_user_message(user_query)
        except Exception as e:
            logger.error(f"Error rewriting user query for text-to-text search: {e}")
            rewritten_query = user_query

        logger.debug(f"User Query: {user_query}")
        logger.debug(f"Rewritten Query: {rewritten_query}")

        return rewritten_query
