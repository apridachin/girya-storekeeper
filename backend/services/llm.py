from typing import List, Dict

from litellm import acompletion

from backend.utils.logger import logger


class LLMService:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        
    async def create_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Create a completion using LLM API"""
        if not messages:
            logger.error("No messages provided for completion")
            raise HTTPException(status_code=400, detail="Messages are required")

        response = await acompletion(
            api_key=self.api_key,
            model=self.model,
             messages=messages
        )
        result = response.choices[0].message.content
        
        logger.debug(
            "Completion created",
            extra={
                "messages": messages,
                "usage": response.get("usage")
            }
        )

        return result


    async def parse_html(self, instructions: str, html: str) -> List[Dict[str, str]]:
        logger.debug(
            "Parsing HTML on the base of instructions",
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
            return result
        except Exception as e:
            logger.error(
                "Error parsing HTML",
                extra={"error": str(e)}
            )
            raise