import json
import re
from enum import Enum

from loguru import logger
from pydantic import BaseModel

from fundus_murag.agent.chat_assistant import ChatAssistant
from fundus_murag.agent.chat_assistant_factory import ChatAssistantFactory
from fundus_murag.agent.prompts.concierge import (
    CONCIERGE_ASSISTANTS_LIST_PLACEHOLDER,
    CONCIERGE_SYSTEM_INSTRUCTION_TEMPLATE,
    FORWARDING_REQUEST_USER_MESSAGE_TEMPLATE,
    PROCESS_ASSISTANT_RESPONSE_USER_MESSAGE_TEMPLATE,
)
from fundus_murag.agent.prompts.db_interaction import DB_INTERACTION_ASSISTANT_SYSTEM_INSTRUCTION
from fundus_murag.agent.prompts.image_analysis import IMAGE_ANALYSIS_ASSISTANT_SYSTEM_INSTRUCTION
from fundus_murag.agent.tools.tools import (
    get_image_analysis_tool,
    get_lex_search_tool,
    get_lookup_tool,
    get_sim_search_tool,
)
from fundus_murag.config import load_config
from fundus_murag.data.dtos.session import SessionHandle


class AssistantType(str, Enum):
    CONCIERGE = "concierge"
    DB_LOOKUP = "db_lookup"
    SIM_SEARCH = "sim_search"
    LEX_SEARCH = "lex_search"
    IMG_ANALYSIS = "img_analysis"


class ConciergeAssistant(BaseModel):
    assistant_type: AssistantType
    internal_id: str
    name: str
    description: str


CONCIERGE_ASSISTANTS: dict[AssistantType, ConciergeAssistant] = {
    AssistantType.DB_LOOKUP: ConciergeAssistant(
        assistant_type=AssistantType.DB_LOOKUP,
        internal_id="db_lookup",
        name="Database Lookup Assistant",
        description="This assistant can retrieve information and statistics about FundusRecords and FundusCollections from the database. For example, it can provide the total number of records or collections or retrieve a specific record by its ID.",
    ),
    AssistantType.SIM_SEARCH: ConciergeAssistant(
        assistant_type=AssistantType.SIM_SEARCH,
        internal_id="sim_search",
        name="Similarity Search Assistant",
        description="This assistant can perform similarity searches on FundusRecords and FundusCollections. For example, it can find records with similar images or titles. Call this assistant if the user does not provide an exact name or ID.",
    ),
    AssistantType.LEX_SEARCH: ConciergeAssistant(
        assistant_type=AssistantType.LEX_SEARCH,
        internal_id="lex_search",
        name="Lexical Search Assistant",
        description="This assistant can perform lexical searches on FundusRecords and FundusCollections. For example, it can find records or collections based on keywords or phrases. Call this assistant if the user provides exact terms or phrases.",
    ),
    AssistantType.IMG_ANALYSIS: ConciergeAssistant(
        assistant_type=AssistantType.IMG_ANALYSIS,
        internal_id="img_analysis",
        name="Image Analysis Assistant",
        description="This assistant can analyze images of FundusRecords and provide information about the image content. For example, it can answer questions about an image, provide detailed descriptions, or read text from images. Call this assistant if the user requests image analysis of a FundusRecord.",
    ),
}


class FundusMultiAgentSystem:
    def __init__(
        self,
        model_name: str | None = None,
    ):
        self._conf = load_config()
        self.model_name = model_name or self._conf.assistant.default_model
        self._assistant_sessions: dict[AssistantType, SessionHandle] = dict()
        self._assistant_factory = ChatAssistantFactory()
        self._build_assistants()

    def _build_assistants(self) -> None:
        logger.info("Building assistants ...")
        for assistant_type in AssistantType:
            system_instruction = None
            tools = None
            match assistant_type:
                case AssistantType.CONCIERGE:
                    system_instruction = CONCIERGE_SYSTEM_INSTRUCTION_TEMPLATE.replace(
                        CONCIERGE_ASSISTANTS_LIST_PLACEHOLDER, self._generate_concierge_assistants_list()
                    )
                    tools = None
                case AssistantType.DB_LOOKUP:
                    system_instruction = DB_INTERACTION_ASSISTANT_SYSTEM_INSTRUCTION
                    tools = [get_lookup_tool()]
                case AssistantType.SIM_SEARCH:
                    system_instruction = DB_INTERACTION_ASSISTANT_SYSTEM_INSTRUCTION
                    tools = [get_sim_search_tool()]
                case AssistantType.LEX_SEARCH:
                    system_instruction = DB_INTERACTION_ASSISTANT_SYSTEM_INSTRUCTION
                    tools = [get_lex_search_tool()]
                case AssistantType.IMG_ANALYSIS:
                    system_instruction = IMAGE_ANALYSIS_ASSISTANT_SYSTEM_INSTRUCTION
                    tools = [get_image_analysis_tool()]
                case _:
                    raise ValueError(f"Unsupported assistant type: {assistant_type}")

            _, session = self._assistant_factory.get_or_create_assistant(
                assistant_name=assistant_type.value.replace("_", " ").upper(),
                model_name=self.model_name,
                system_instruction=system_instruction,
                available_tools=tools,
                session=None,  # start a new session
            )
            self._assistant_sessions[assistant_type] = session
            logger.info(f"{assistant_type.upper()} Assistant built successfully.")

    def _generate_concierge_assistants_list(self) -> str:
        assistants_list = """
# Your Assistants

You have the following assistants at your disposal:
"""
        for assistant in CONCIERGE_ASSISTANTS.values():
            assistants_list += f"""
**{assistant.name}**
   name: `{assistant.internal_id}`
   description: {assistant.description}
"""
        return assistants_list

    def _get_assistant(self, assistant_type: AssistantType) -> ChatAssistant:
        if assistant_type not in self._assistant_sessions:
            raise KeyError(f"{assistant_type.upper()} Assistant not found.")
        session = self._assistant_sessions[assistant_type]
        assistant, _ = self._assistant_factory.get_or_create_assistant(
            session=session.session_id,
        )
        return assistant

    def _parse_forwarding_request(self, concierge_response: str) -> dict[str, str] | None:
        resp = concierge_response.encode().decode("unicode_escape").replace("\n", " ")

        mandatory_keys = ["assistant", "user_request", "context"]

        # Regex to check if the response contains JSON with or without markdown fences
        json_pattern = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```|(\{.*?\})")

        match = json_pattern.search(resp)
        if match:
            json_str = match.group(1) if match.group(1) else match.group(2)
            try:
                json_obj = json.loads(json_str)
                if all(key in json_obj for key in mandatory_keys):
                    return json_obj
                else:
                    msg = f"Malformed Forwarding Request: Missing mandatory keys. {json_obj}"
                    logger.error(msg)
                    raise ValueError(msg)
            except json.JSONDecodeError:
                logger.debug("Found JSON-like content, but failed to parse it")

        # If no JSON found or parsing failed, try a more aggressive approach
        try:
            # Look for JSON objects in the response text
            json_start = resp.find("{")
            json_end = resp.rfind("}")
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = resp[json_start : json_end + 1]
                json_obj = json.loads(json_str)
                if all(key in json_obj for key in mandatory_keys):
                    return json_obj
                else:
                    msg = f"Malformed Forwarding Request: Missing mandatory keys. {json_obj}"
                    logger.error(msg)
                    raise ValueError(msg)
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.debug("Failed to extract JSON with the fallback method")

        return None

    def _forward_user_request(
        self,
        forwarding_request: dict[str, str],
        user_request: str,
        base64_image: str | None = None,
    ) -> str:
        assistant_name = forwarding_request["assistant"]
        user_request = forwarding_request["user_request"]
        context = forwarding_request["context"]

        try:
            assistant_type = AssistantType(assistant_name)
        except ValueError:
            raise ValueError(f"Unsupported Assistant name: {assistant_name}")

        assistant = self._get_assistant(assistant_type)

        message = FORWARDING_REQUEST_USER_MESSAGE_TEMPLATE.format(
            USER_REQUEST=user_request,
            CONTEXT=context,
        )
        assistant_response = assistant.send_user_message(text_message=message, base64_image=base64_image)

        return assistant_response

    def _process_assistant_response(
        self,
        assistant_response: str,
        original_user_request: str,
        forwarded_request: dict[str, str],
    ) -> str:
        concierge_assistant = self._get_assistant(AssistantType.CONCIERGE)

        assistant_response_message = PROCESS_ASSISTANT_RESPONSE_USER_MESSAGE_TEMPLATE.format(
            ORIGINAL_USER_REQUEST=original_user_request,
            FORWARDED_REQUEST=json.dumps(forwarded_request, indent=2),
            ASSISTANT_NAME=forwarded_request["assistant"],
            ASSISTANT_RESPONSE=assistant_response,
        )

        concierge_response = concierge_assistant.send_user_message(text_message=assistant_response_message)

        return concierge_response

    def handle_user_request(
        self,
        user_request: str,
        base64_image: str | None = None,
    ) -> str:
        # first, the user request is sent to the concierge
        concierge_assistant = self._get_assistant(AssistantType.CONCIERGE)
        concierge_response = concierge_assistant.send_user_message(text_message=user_request, base64_image=base64_image)

        forwarding_request = self._parse_forwarding_request(concierge_response)
        while forwarding_request is not None:
            # if the response contains a forwarding request, forward the user request to the appropriate assistant
            assistant_response = self._forward_user_request(forwarding_request, user_request, base64_image)

            # send the assistant response back to the concierge to generate the user response or another forwarding request
            concierge_response = self._process_assistant_response(
                assistant_response=assistant_response,
                original_user_request=user_request,
                forwarded_request=forwarding_request,
            )
            forwarding_request = self._parse_forwarding_request(concierge_response)

        return concierge_response
