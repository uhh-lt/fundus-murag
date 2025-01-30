from abc import ABC, abstractmethod
from typing import Literal

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
    @abstractmethod
    def _generate_vqa_prompt(record: FundusRecordInternal, question: str):
        pass

    @staticmethod
    @abstractmethod
    def _generate_image_captioning_prompt(record: FundusRecordInternal,bdetailed: bool = False):
        pass

    @staticmethod
    @abstractmethod
    def _get_text_response(response) -> str:
        pass
