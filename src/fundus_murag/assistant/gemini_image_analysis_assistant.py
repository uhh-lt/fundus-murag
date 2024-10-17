import google.generativeai as genai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    GenerationResponse,
    Part,
)
import vertexai
from google.oauth2.service_account import Credentials
from loguru import logger

from fundus_murag.assistant.prompt import (
    GEMINI_IMAGE_ANALYSIS_VQA_SYSTEM_INSTRUCTION,
    GEMINI_IMAGE_ANALYSIS_IC_SYSTEM_INSTRUCTION,
)
from fundus_murag.config.config import load_config
from typing import Literal

from fundus_murag.data.dto import FundusRecordInternal
from fundus_murag.data.vector_db import VectorDB
from fundus_murag.singleton_meta import SingletonMeta

import json

GEMINI_GENERATION_CONFIG = GenerationConfig(
    candidate_count=1,
    temperature=1.0,
    top_p=0.95,
    max_output_tokens=2048,
)


MODEL_NAME = "gemini-1.5-pro-002"


class GeminiImageAnalysisAssistant(metaclass=SingletonMeta):
    def __init__(self, model_name: str | None = None):
        if model_name is None:
            model_name = MODEL_NAME
        conf = load_config()
        creds = Credentials.from_service_account_file(
            conf.google_application_credentials_file
        )

        vertexai.init(
            credentials=creds,
            project=conf.google_project_id,
            location="europe-west3",
        )
        genai.configure(credentials=creds)
        self._vqa_model: GenerativeModel = self._load_model(model_name, "vqa")
        self._image_captioning_model: GenerativeModel = self._load_model(
            model_name, "ic"
        )

        self._vdb = VectorDB()

    def _load_model(
        self, model_name: str, type: Literal["vqa", "ic"]
    ) -> GenerativeModel:
        model_name = model_name.lower()
        if "/" in model_name:
            model_name = model_name.split("/")[-1]

        if type == "vqa":
            system_instruction = GEMINI_IMAGE_ANALYSIS_VQA_SYSTEM_INSTRUCTION
        elif type == "ic":
            system_instruction = GEMINI_IMAGE_ANALYSIS_IC_SYSTEM_INSTRUCTION
        else:
            raise NotImplementedError(f"Unsupported model type: {type}")

        model = GenerativeModel(
            model_name=model_name,
            generation_config=GEMINI_GENERATION_CONFIG,
            system_instruction=system_instruction,
        )
        return model

    def answer_question_about_fundus_record_image(
        self,
        question: str,
        murag_id: str,
    ) -> str:
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
        text_parts = [self._generate_vqa_prompt(record, question)]
        image_parts = [Part.from_data(base64_image, mime_type="image/png")]  # type: ignore

        prompt = text_parts + image_parts
        try:
            response = self._vqa_model.generate_content(prompt)  # type: ignore
            return self._get_text_response(response)
        except Exception as e:
            msg = f"Error performing VQA: {e}"
            logger.error(msg)
            return msg

    def generate_caption_for_fundus_record_image(
        self,
        murag_id: str,
        detailled: bool = False,
    ) -> str:
        """
        Generates a caption for the image of a `FundusRecord` specified by the given `murag_id`.

        Args:
            murag_id: The murag_id of the `FundusRecord` that contains the image to be captioned.
            detailled: Whether the generated image caption should be detailed or not, i.e., concise.

        Returns:
            The generated caption for the image.
        """
        record = self._vdb.get_fundus_record_internal_by_murag_id(murag_id)
        base64_image = record.base64_image
        text_parts = [self._generate_image_captioning_prompt(record)]
        image_parts = [Part.from_data(base64_image, mime_type="image/png")]  # type: ignore

        prompt = text_parts + image_parts
        try:
            response = self._image_captioning_model.generate_content(prompt)  # type: ignore
            return self._get_text_response(response)
        except Exception as e:
            msg = f"Error generating an image caption: {e}"
            logger.error(msg)
            return msg

    @staticmethod
    def _generate_image_captioning_prompt(
        record: FundusRecordInternal,
        detailled: bool = False,
    ) -> Part:
        prompt = f"Generate a {'detailed' if detailled else 'concise'} caption "
        prompt += "for the image considering the following metadata.\n"
        prompt += "# Metadata as JSON\n"
        prompt += f"```json\n{json.dumps(record.details, indent=2)}\n```\n"

        return Part.from_text(prompt)

    @staticmethod
    def _generate_vqa_prompt(
        record: FundusRecordInternal,
        question: str,
    ) -> Part:
        prompt = "# Question\n"
        prompt += f"'''\n{question}\n'''\n"
        prompt += "# Metadata as JSON\n"
        prompt += f"```json\n{json.dumps(record.details, indent=2)}\n```\n"

        return Part.from_text(prompt)

    def _get_text_response(self, response: GenerationResponse) -> str:
        try:
            return response.candidates[0].text
        except Exception:
            raise ValueError("No text response found.")