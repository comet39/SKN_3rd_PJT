# interface.py - Auto-generated
"""
LLM interface for interacting with various language models
"""
import logging
import os
import json
from typing import Dict, Any, Optional, List, Union, Generator, AsyncGenerator
import openai
from openai import AsyncOpenAI
# import anthropic
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from modules.llm.prompts import SYSTEM_PROMPT, CHAT_PROMPT, ANALYZE_PROMPT

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for language model providers"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize LLM interface
        
        Args:
            model_name: Name of the model to use
        """
        self.model_name = model_name or settings.DEFAULT_LLM_MODEL
        
        # Initialize clients
        if settings.OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.async_openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.openai_client = None
            self.async_openai_client = None
        
        # if settings.ANTHROPIC_API_KEY:
        #     self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        # else:
        #     self.anthropic_client = None
            
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.gemini_client = genai
        else:
            self.gemini_client = None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(
        self,
        query: str,
        context: str,
        references: List[Dict[str, Any]],
        country: Optional[str] = None,
        topic: Optional[str] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[Dict[str, Any], None]]:
        """
        Generate response from LLM
        
        Args:
            query: User query
            context: RAG context
            references: List of reference information
            country: Optional country context
            topic: Optional topic context
            system_prompt: Optional system prompt override
            stream: Whether to stream the response
            
        Returns:
            LLM response or stream
        """
        # Prepare message with context
        messages = self._prepare_messages(
            query=query, 
            context=context, 
            references=references,
            country=country,
            topic=topic,
            system_prompt=system_prompt
        )
        
        # Select model provider based on model name
        if self.model_name.startswith("gpt-") and self.openai_client:
            # OpenAI models
            if stream:
                return self._stream_openai_response(messages)
            else:
                return await self._generate_openai_response(messages)
                
        # elif self.model_name.startswith("claude-") and self.anthropic_client:
            # Anthropic models
            # if not self.anthropic_client:
            #     logger.error("Anthropic API key not configured")
            #     return "Error: Anthropic API not configured."
                
            # if stream:
            #     return self._stream_anthropic_response(messages)
            # else:
            #     return await self._generate_anthropic_response(messages)
        
        elif self.model_name.startswith("gemini-") and self.gemini_client:
            # Google Gemini models
            if stream:
                return self._stream_gemini_response(messages)
            else:
                return await self._generate_gemini_response(messages)
        
        else:
            logger.error(f"Unsupported model: {self.model_name}")
            return "Error: Unsupported model."
    
    def _prepare_messages(
        self,
        query: str,
        context: str,
        references: List[Dict[str, Any]],
        country: Optional[str] = None,
        topic: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Prepare messages for LLM API
        
        Args:
            query: User query
            context: RAG context
            references: List of reference information
            country: Optional country context
            topic: Optional topic context
            system_prompt: Optional system prompt override
            
        Returns:
            List of messages for LLM API
        """
        # Prepare system prompt
        if not system_prompt:
            system_prompt = SYSTEM_PROMPT
        
        # Add country and topic if available
        context_info = ""
        if country:
            context_info += f"Country: {country}\n"
        if topic:
            context_info += f"Topic: {topic}\n"
        
        # Format references for prompt
        ref_text = ""
        for i, ref in enumerate(references):
            ref_text += f"[{i+1}] {ref.get('title')} ({ref.get('source')})\n"
        
        # Use chat prompt template
        user_prompt = CHAT_PROMPT.format(
            query=query,
            context=context,
            context_info=context_info,
            references=ref_text
        )
        
        # Create message list based on provider
        if self.model_name.startswith("gpt-"):
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        else:
            # For Anthropic, combine system and user prompt
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        
        return messages
    
    async def _generate_openai_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate response from OpenAI API
        
        Args:
            messages: List of messages
            
        Returns:
            LLM response text
        """
        try:
            response = await self.async_openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return f"Error generating response: {str(e)}"
    
    async def _stream_openai_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response from OpenAI API
        
        Args:
            messages: List of messages
            
        Yields:
            Response chunks
        """
        try:
            stream = await self.async_openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {
                        "type": "token",
                        "content": chunk.choices[0].delta.content
                    }
            
            # Final chunk to signal end of stream
            yield {"type": "end", "content": ""}
            
        except Exception as e:
            logger.error(f"Error streaming OpenAI response: {e}")
            yield {"type": "token", "content": f"Error: {str(e)}"}
            yield {"type": "end", "content": ""}
    
    # async def _generate_anthropic_response(self, messages: List[Dict[str, str]]) -> str:
    #     """
    #     Generate response from Anthropic API
        
    #     Args:
    #         messages: List of messages
            
    #     Returns:
    #         LLM response text
    #     """
    #     try:
    #         system_message = messages[0]["content"]
    #         user_message = messages[1]["content"]
            
    #         response = await self.anthropic_client.messages.create(
    #             model=self.model_name,
    #             system=system_message,
    #             messages=[{"role": "user", "content": user_message}],
    #             max_tokens=1000
    #         )
            
    #         return response.content[0].text
    #     except Exception as e:
    #         logger.error(f"Error generating Anthropic response: {e}")
    #         return f"Error generating response: {str(e)}"
    
    # async def _stream_anthropic_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
    #     """
    #     Stream response from Anthropic API
        
    #     Args:
    #         messages: List of messages
            
    #     Yields:
    #         Response chunks
    #     """
    #     try:
    #         system_message = messages[0]["content"]
    #         user_message = messages[1]["content"]
            
    #         stream = await self.anthropic_client.messages.create(
    #             model=self.model_name,
    #             system=system_message,
    #             messages=[{"role": "user", "content": user_message}],
    #             max_tokens=1000,
    #             stream=True
    #         )
            
    #         async for chunk in stream:
    #             if chunk.delta.text:
    #                 yield {
    #                     "type": "token",
    #                     "content": chunk.delta.text
    #                 }
            
    #         # Final chunk to signal end of stream
    #         yield {"type": "end", "content": ""}
            
    #     except Exception as e:
    #         logger.error(f"Error streaming Anthropic response: {e}")
    #         yield {"type": "token", "content": f"Error: {str(e)}"}
    #         yield {"type": "end", "content": ""}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query with LLM to extract structured information
        
        Args:
            query: User query
            
        Returns:
            Dict with analysis results
        """
        messages = [
            {"role": "system", "content": ANALYZE_PROMPT},
            {"role": "user", "content": query}
        ]
        
        try:
            response = await self.async_openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                analysis = json.loads(response_text)
                return analysis
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from LLM analysis response: {response_text}")
                # Return basic analysis
                return {
                    "query": query,
                    "country": None,
                    "topic": None,
                    "keywords": query.split(),
                    "is_question": "?" in query
                }
                
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            # Return basic analysis
            return {
                "query": query,
                "country": None,
                "topic": None,
                "keywords": query.split(),
                "is_question": "?" in query
            }