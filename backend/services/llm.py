from typing import List, Dict

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from backend.utils.logger import logger


class CompletionRequest(BaseModel):
    model: str = "gpt-4o"
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 500


class LLMService:
    def __init__(self, api_url: str, api_key: str):
        self.base_url = api_url
        self.api_key = api_key
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Create a completion using LLM API"""
        if not messages:
            logger.error("No messages provided for completion")
            raise HTTPException(status_code=400, detail="Messages are required")
            
        request = CompletionRequest(
            messages=messages,
            **kwargs
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=request.model_dump(),
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            completion = result["choices"][0]["message"]["content"]
            
            logger.debug(
                "Completion created successfully",
                extra={
                    "completion_length": len(completion),
                    "finish_reason": result["choices"][0].get("finish_reason")
                }
            )
            return completion


    async def parse_html(self, instructions: str, html: str) -> List[Dict[str, str]]:
        logger.debug(
            "Parsing HTML with instructions",
            extra={
                "instruction_length": len(instructions),
                "html_length": len(html)
            }
        )
        
        system_message = {
            "role": "system",
            "content": "You are a web scrapper. You are a webscrapper. Answer questions about the the page."
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
            result = await self.create_completion(messages=[system_message, user_message])
            logger.debug(
                "HTML parsing completed",
                extra={
                    "result_length": len(result),
                    "is_not_found": result == "NOT FOUND"
                }
            )
            return result
        except Exception as e:
            logger.error(
                "Error parsing HTML",
                extra={"error": str(e)}
            )
            raise