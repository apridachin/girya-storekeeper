import json
from typing import List, Dict

from litellm import acompletion
from fastapi import HTTPException
from openai import BaseModel

from backend.utils.logger import logger


class LLMService:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        
    async def create_completion(
        self,
        messages: List[Dict[str, str]],
        response_format: BaseModel = None,
        **kwargs
    ) -> BaseModel | None:
        """Create a completion using LLM API"""
        if not messages:
            logger.error("No messages provided for completion")
            raise HTTPException(status_code=400, detail="Messages are required")

        response = await acompletion(
            api_key=self.api_key,
            model=self.model,
            messages=messages,
            response_format=response_format,
        )
        result = response.choices[0].message.content
        if response_format:
            try: 
                result = response_format.model_validate(json.loads(result))
            except TypeError as e:
                logger.warning(
                    "Failed to parse response",
                    extra={
                        "response": result,
                        "error": str(e)
                    }
                )
                result = None
                

        logger.debug(
            "Completion created",
            extra={
                "messages": messages,
                "usage": response.get("usage")
            }
        )

        return result


    async def parse_html(self, instructions: str, html: str, response_format: BaseModel = None) -> BaseModel | None:
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
            result = await self.create_completion(messages=[system_message, user_message], response_format=response_format)
            return result
        except Exception as e:
            logger.error(
                "Error parsing HTML",
                extra={"error": str(e)}
            )
            raise