import json
from enum import Enum

from loguru import logger

from fundus_murag.agent.chat_assistant import ChatAssistant
from fundus_murag.agent.chat_assistant_factory import ChatAssistantFactory
from fundus_murag.agent.prompts.image_analysis import (
    IMAGE_ANALYSIS_IC_SYSTEM_INSTRUCTION,
    IMAGE_ANALYSIS_OCR_SYSTEM_INSTRUCTION,
    IMAGE_ANALYSIS_OD_SYSTEM_INSTRUCTION,
    IMAGE_ANALYSIS_VQA_SYSTEM_INSTRUCTION,
)
from fundus_murag.data.dtos.fundus import FundusRecordInternal
from fundus_murag.data.vector_db import VectorDB


class ImageAnalysisTask(str, Enum):
    VQA = "vqa"
    IC = "ic"
    OCR = "ocr"
    OD = "od"


class ImageAnalyzer:
    def __init__(self):
        self._vdb = VectorDB()
        self._factory = ChatAssistantFactory()

    def _get_image_analysis_assistant(self, task: ImageAnalysisTask) -> ChatAssistant:
        match task:
            case ImageAnalysisTask.VQA:
                system_instruction = IMAGE_ANALYSIS_VQA_SYSTEM_INSTRUCTION
            case ImageAnalysisTask.IC:
                system_instruction = IMAGE_ANALYSIS_IC_SYSTEM_INSTRUCTION
            case ImageAnalysisTask.OCR:
                system_instruction = IMAGE_ANALYSIS_OCR_SYSTEM_INSTRUCTION
            case ImageAnalysisTask.OD:
                system_instruction = IMAGE_ANALYSIS_OD_SYSTEM_INSTRUCTION
            case _:
                raise ValueError(f"Unsupported task type: {task}")

        assistant, _ = self._factory.get_or_create_assistant(
            assistant_name="Image Analyzer",
            model_name=None,  # Use the default model
            system_instruction=system_instruction,
            available_tools=None,  # No tools!
            session=None,  # Start a new session
        )
        return assistant

    def answer_question_about_fundus_record_image(self, question: str, murag_id: str) -> str:
        """
        Generates an answer to the given question about the image of a `FundusRecord` specified by the given `murag_id`.
        In other words, this function performs Visual Question Answering (VQA) on the image of a `FundusRecord`.

        Args:
            question: The question to be answered.
            murag_id: The murag_id of the `FundusRecord` that contains the image to be analyzed to generate the answer to the question.

        Returns:
            The answer to the question.
        """
        record = self._vdb.get_fundus_record_internal_by_murag_id(murag_id)
        base64_image = record.base64_image

        try:
            user_prompt = self.generate_vqa_prompt(record, question)
            assistant = self._get_image_analysis_assistant(ImageAnalysisTask.VQA)
            response_text = assistant.send_user_message(user_prompt, base64_image)
            return response_text

        except Exception as e:
            msg = f"Error performing VQA: {e}"
            logger.error(msg)
            return msg

    def generate_caption_for_fundus_record_image(self, murag_id: str, detailed: bool = False) -> str:
        """
        Generates a caption for the image of a `FundusRecord` specified by the given `murag_id`.

        Args:
            murag_id: The murag_id of the `FundusRecord` that contains the image to be captioned.
            detailed: Whether the generated image caption should be detailed or concise.

        Returns:
            The generated caption for the image.
        """
        record = self._vdb.get_fundus_record_internal_by_murag_id(murag_id)
        base64_image = record.base64_image

        try:
            user_prompt = self.generate_image_captioning_prompt(record, detailed)
            assistant = self._get_image_analysis_assistant(ImageAnalysisTask.IC)
            response_text = assistant.send_user_message(user_prompt, base64_image)
            return response_text

        except Exception as e:
            msg = f"Error generating an image caption: {e}"
            logger.error(msg)
            return msg

    def extract_text_from_fundus_record_image(self, murag_id: str) -> str:
        """
        Perform OCR on the image of a `FundusRecord` specified by the given `murag_id`.

        Args:
            murag_id: The murag_id of the `FundusRecord` that contains the image to perform OCR on.

        Returns:
            The extracted text from the image.
        """
        record = self._vdb.get_fundus_record_internal_by_murag_id(murag_id)
        base64_image = record.base64_image

        try:
            user_prompt = self.generate_ocr_prompt(record)
            assistant = self._get_image_analysis_assistant(ImageAnalysisTask.OCR)
            response_text = assistant.send_user_message(user_prompt, base64_image)
            return response_text

        except Exception as e:
            msg = f"Error performing OCR: {e}"
            logger.error(msg)
            return msg

    def detect_objects_in_fundus_record_image(self, murag_id: str) -> str:
        """
        Perform object detection on the image of a `FundusRecord` specified by the given `murag_id`.

        Args:
            murag_id: The murag_id of the `FundusRecord` that contains the image to perform object detection on.

        Returns:
            The detected objects in the image.
        """
        record = self._vdb.get_fundus_record_internal_by_murag_id(murag_id)
        base64_image = record.base64_image

        try:
            user_prompt = self.generate_od_prompt(record)
            assistant = self._get_image_analysis_assistant(ImageAnalysisTask.OD)
            response_text = assistant.send_user_message(user_prompt, base64_image)
            return response_text

        except Exception as e:
            msg = f"Error performing object detection: {e}"
            logger.error(msg)
            return msg

    @staticmethod
    def generate_vqa_prompt(record: FundusRecordInternal, question: str) -> str:
        prompt = "# Question\n\n"
        prompt += f"'''\n{question}\n'''\n\n"
        prompt += "# Metadata as JSON\n\n"
        prompt += f"```json\n{json.dumps(record.details, indent=2)}\n```\n"
        return prompt

    @staticmethod
    def generate_image_captioning_prompt(record: FundusRecordInternal, detailed: bool = False) -> str:
        style = "detailed" if detailed else "concise"
        prompt = f"Generate a {style} caption for the image considering the metadata.\n\n"
        prompt += "# Metadata as JSON\n\n"
        prompt += f"```json\n{json.dumps(record.details, indent=2)}\n```\n"
        return prompt

    @staticmethod
    def generate_ocr_prompt(record: FundusRecordInternal) -> str:
        prompt = "Extract all text from the image considering the metadata.\n\n"
        prompt += "# Metadata as JSON\n\n"
        prompt += f"```json\n{json.dumps(record.details, indent=2)}\n```\n"
        return prompt

    @staticmethod
    def generate_od_prompt(record: FundusRecordInternal) -> str:
        prompt = "Detect all objects in the image considering the metadata.\n\n"
        prompt += "# Metadata as JSON\n\n"
        prompt += f"```json\n{json.dumps(record.details, indent=2)}\n```\n"
        return prompt
