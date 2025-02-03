import openai
from loguru import logger
import json
from typing import TypedDict, Literal

from fundus_murag.assistant.prompt import (
    IMAGE_ANALYSIS_VQA_SYSTEM_INSTRUCTION,
    IMAGE_ANALYSIS_IC_SYSTEM_INSTRUCTION,
)
from fundus_murag.config.config import load_config
from fundus_murag.data.dto import FundusRecordInternal
from fundus_murag.data.vector_db import VectorDB
from fundus_murag.singleton_meta import SingletonMeta

from base_image_analysis_assistant import BaseImageAnalysisAssistant

OPENAI_MODEL = "gpt-4o-mini"

class ModelConfig(TypedDict):
    model_name: str
    system_instruction: str
    temperature: float
    max_tokens: int

BASE_MODEL_CONFIG: ModelConfig = {
    "model_name": "",
    "system_instruction": "",
    "temperature": 1.0,
    "max_tokens": 2048,
}

class OpenAIImageAnalysisAssistant(BaseImageAnalysisAssistant, metaclass=SingletonMeta):

    def __init__(self, model_name: str | None = None):
        conf = load_config()
        openai.api_key = conf.open_ai_api_key
        self._vdb = VectorDB()

        # defult unless we have another model
        self._default_model_name = model_name if model_name else OPENAI_MODEL

        self._vqa_model: ModelConfig = self._load_model(self._default_model_name, "vqa")
        self._ic_model: ModelConfig = self._load_model(self._default_model_name, "ic")

    def _load_model(self, model_name: str, model_type: Literal["vqa", "ic"]) -> ModelConfig:
        if model_type == "vqa":
            system_instruction = IMAGE_ANALYSIS_VQA_SYSTEM_INSTRUCTION
        elif model_type == "ic":
            system_instruction = IMAGE_ANALYSIS_IC_SYSTEM_INSTRUCTION
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        model_config = BASE_MODEL_CONFIG.copy()
        model_config["model_name"] = model_name
        model_config["system_instruction"] = system_instruction

        return model_config

    def answer_question_about_fundus_record_image(self, question: str, murag_id: str) -> str:
        
        record = self._vdb.get_fundus_record_internal_by_murag_id(murag_id)
        base64_image = record.base64_image

        try:
            vqa_config = self._vqa_model
            system_instruction = vqa_config["system_instruction"]
            model_name = vqa_config["model_name"]

            user_prompt = self._generate_vqa_prompt(record, question)

            messages = self._build_prompt_messages(
                system_instruction=system_instruction,
                user_text=user_prompt,
                base64_image=base64_image,
                detail="auto",  
            )

            response = openai.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=vqa_config["temperature"],
                max_tokens=vqa_config["max_tokens"],
            )
            return self._get_text_response(response)

        except Exception as e:
            msg = f"Error performing VQA: {e}"
            logger.error(msg)
            return msg

    def generate_caption_for_fundus_record_image(self, murag_id: str, detailed: bool = False) -> str:
        
        record = self._vdb.get_fundus_record_internal_by_murag_id(murag_id)
        base64_image = record.base64_image

        try:
            ic_config = self._ic_model
            system_instruction = ic_config["system_instruction"]
            model_name = ic_config["model_name"]

            user_prompt = self._generate_image_captioning_prompt(record, detailed)

            messages = self._build_prompt_messages(
                system_instruction=system_instruction,
                user_text=user_prompt,
                base64_image=base64_image,
                detail="auto",
            )

            response = openai.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=ic_config["temperature"],
                max_tokens=ic_config["max_tokens"],
            )
            return self._get_text_response(response)

        except Exception as e:
            msg = f"Error generating an image caption: {e}"
            logger.error(msg)
            return msg


    @staticmethod
    def _build_prompt_messages(
        system_instruction: str,
        user_text: str,
        base64_image: str,
        detail: str = "auto",
    ):
        return [
            {
                "role": "system",
                "content": system_instruction,
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": detail,
                        },
                    },
                ],
            },
        ]

    @staticmethod
    def _generate_vqa_prompt(record: FundusRecordInternal, question: str) -> str:
        return BaseImageAnalysisAssistant.generate_vqa_prompt(record, question)

    @staticmethod
    def _generate_image_captioning_prompt(record: FundusRecordInternal, detailed: bool = False) -> str:
        return BaseImageAnalysisAssistant.generate_image_captioning_prompt(record, detailed)

    @staticmethod
    def _get_text_response(response) -> str:
        try:
            return response.choices[0].message.content
        except (AttributeError, IndexError) as e:
            raise ValueError(f"No text response found in OpenAI response. Error: {e}")