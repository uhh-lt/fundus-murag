from abc import ABC, abstractmethod
from typing import Literal
import json

from fundus_murag.data.dto import FundusRecordInternal

class BaseImageAnalysisAssistant(ABC):
    @abstractmethod
    def __init__(self, model_name: str | None = None):
        pass

    @abstractmethod
    def _load_model(self, model_name: str, model_type: Literal["vqa", "ic"]):
        pass

    @abstractmethod
    def answer_question_about_fundus_record_image(self, question: str, murag_id: str) -> str:
        pass

    
    @abstractmethod
    def generate_caption_for_fundus_record_image(self, murag_id: str, detailed: bool = False) -> str:
        pass

    @staticmethod
    def generate_vqa_prompt(record: FundusRecordInternal, question: str) -> str:
        prompt = "# Question\n"
        prompt += f"'''\n{question}\n'''\n"
        prompt += "# Metadata as JSON\n"
        prompt += f"```json\n{json.dumps(record.details, indent=2)}\n```\n"
        return prompt

    @staticmethod
    def generate_image_captioning_prompt(record: FundusRecordInternal, detailed: bool = False) -> str:
        style = "detailed" if detailed else "concise"
        prompt = f"Generate a {style} caption for the image considering the metadata.\n"
        prompt += "# Metadata as JSON\n"
        prompt += f"```json\n{json.dumps(record.details, indent=2)}\n```\n"
        return prompt

    @staticmethod
    @abstractmethod
    def _get_text_response(response) -> str:
        pass
