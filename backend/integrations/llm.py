import json
from typing import Dict

import litellm
from openai import AsyncOpenAI
from fastapi import HTTPException
from pydantic import BaseModel

from backend.utils.logger import logger


class HTMLParsingException(Exception):
    pass


class LLMClient:
    def __init__(self, base_url: str | None, api_key: str, provider: str, model: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        litellm.api_key = self.client.api_key
        litellm.api_base = self.client.base_url
        self.provider = provider
        self.model = model

    async def create_completion(
        self,
        model: str,
        messages: list[Dict[str, str]],
    ) -> str:
        """Create a completion using LLM API"""
        if not messages:
            logger.error("No messages provided for completion")
            raise HTTPException(status_code=400, detail="Messages are required")

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        result = response.choices[0].message.content

        logger.debug(
            "Completion created",
            extra={
                "completion_tokens": response.usage.completion_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        )

        return result

    async def complete(
        self,
        model: str,
        provider: str,
        messages: list[Dict[str, str]],
    ):
        """Complete a text using LLM API"""
        response = await litellm.acompletion(
            model=provider + '/' + model, 
            messages=messages,
            response_format={"type": "json_object"},
        )   
        result = response.choices[0].message.content

        logger.debug(
            "Litellm completion created",
            extra={
                "model": model,
                "provider": provider,
                "completion_tokens": response.usage.completion_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        )

        return result

    async def parse_html(
        self,
        html: str,
        instructions: str,
        response_format: BaseModel,
    ) -> BaseModel:
        logger.debug(
            "Parsing HTML on the base of instructions",
            extra={
                "instruction_length": len(instructions),
                "html_length": len(html)
            }
        )
        
        system_message = {
            "role": "system",
            "content": "You are a web scrapper. Answer questions about the the page."
        }
        
        user_message = {
            "role": "user",
            "content": (
                f"Instructions: {instructions}"
                "\n\n"
                f" HTML page: {html}"
            )
        }

        try:
            completion = await self.complete(
                model=self.model,
                provider=self.provider,
                messages=[system_message, user_message],
            )
            result = response_format.model_validate(json.loads(completion))
            return result
        except Exception as e:
            logger.error(
                "Error parsing HTML",
                extra={"error": str(e)}
            )
            raise HTMLParsingException() from e