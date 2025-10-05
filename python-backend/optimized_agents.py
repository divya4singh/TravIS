"""
Optimized agent wrapper for free tier OpenAI usage.
Implements rate limiting, context engineering, and caching.
"""

import asyncio
import hashlib
import json
from typing import Any, Dict, List, Optional, Union
from agents import Agent, Runner, RunContextWrapper
import config

class OptimizedAgent:
    """Wrapper around OpenAI agents with optimizations for free tier usage."""
    
    def __init__(self, agent: Agent, use_fast_model: bool = True):
        self.agent = agent
        self.use_fast_model = use_fast_model
        self.model = config.FAST_MODEL if use_fast_model else config.PREMIUM_MODEL
        
        # Override the agent's model for free tier optimization
        if use_fast_model:
            self.agent.model = config.FAST_MODEL
    
    async def run_with_optimization(
        self, 
        input_data: Union[str, List[Dict[str, Any]]], 
        context: Optional[Any] = None,
        max_retries: int = config.MAX_RETRIES
    ) -> Any:
        """Run agent with rate limiting, caching, and context optimization."""
        
        # Create cache key
        cache_key = self._create_cache_key(input_data, context)
        
        # Check cache first
        cached_response = config.get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        # Apply rate limiting
        await config.rate_limiter.wait()
        
        # Optimize context and input
        optimized_input = self._optimize_input(input_data)
        optimized_context = self._optimize_context(context)
        
        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(max_retries):
            try:
                # Use the original Runner.run method
                result = await Runner.run(
                    self.agent, 
                    optimized_input, 
                    context=optimized_context
                )
                
                # Cache successful response
                config.cache_response(cache_key, result)
                return result
                
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = config.RETRY_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    # Return a fallback response for free tier limits
                    return self._create_fallback_response(input_data, str(e))
        
        return self._create_fallback_response(input_data, str(last_exception))
    
    def _create_cache_key(self, input_data: Any, context: Any) -> str:
        """Create a cache key from input and context."""
        key_data = {
            'input': str(input_data),
            'context': str(context) if context else None,
            'agent': self.agent.name,
            'model': self.model
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _optimize_input(self, input_data: Union[str, List[Dict[str, Any]]]) -> Union[str, List[Dict[str, Any]]]:
        """Optimize input for free tier usage."""
        if isinstance(input_data, str):
            # Truncate long inputs
            if len(input_data) > config.MAX_CONTEXT_LENGTH:
                input_data = input_data[:config.MAX_CONTEXT_LENGTH] + "..."
            return input_data
        
        elif isinstance(input_data, list):
            # Limit conversation history
            if len(input_data) > config.MAX_CONVERSATION_HISTORY:
                # Keep the first message and last N messages
                optimized = [input_data[0]] + input_data[-(config.MAX_CONVERSATION_HISTORY-1):]
                return optimized
            
            # Truncate individual messages
            optimized = []
            for item in input_data:
                if isinstance(item, dict) and 'content' in item:
                    content = item['content']
                    if len(content) > config.MAX_CONTEXT_LENGTH:
                        item = item.copy()
                        item['content'] = content[:config.MAX_CONTEXT_LENGTH] + "..."
                optimized.append(item)
            return optimized
        
        return input_data
    
    def _optimize_context(self, context: Any) -> Any:
        """Optimize context for free tier usage."""
        if context is None:
            return context
        
        # If context has a model_dump method (Pydantic model)
        if hasattr(context, 'model_dump'):
            context_dict = context.model_dump()
            # Keep only essential fields
            essential_fields = ['passenger_name', 'confirmation_number', 'flight_number', 'booking_reference']
            optimized_dict = {k: v for k, v in context_dict.items() if k in essential_fields}
            
            # Create a new context with only essential fields
            if hasattr(context, '__class__'):
                return context.__class__(**optimized_dict)
        
        return context
    
    def _create_fallback_response(self, input_data: Any, error: str) -> Any:
        """Create a fallback response when API calls fail."""
        # Create a simple response object that mimics the expected structure
        class FallbackResponse:
            def __init__(self, message: str):
                self.final_output = message
                self.new_items = []
                self.to_input_list = lambda: []
        
        fallback_message = (
            "I apologize, but I'm experiencing high demand right now. "
            "Please try again in a moment. For immediate assistance, you can: "
            "1. Check your booking reference directly, "
            "2. Contact our support line, or "
            "3. Try again in a few minutes."
        )
        
        return FallbackResponse(fallback_message)

def create_optimized_agent(agent: Agent, use_fast_model: bool = True) -> OptimizedAgent:
    """Create an optimized agent wrapper."""
    return OptimizedAgent(agent, use_fast_model)

# Context engineering utilities
class ContextManager:
    """Manages conversation context efficiently."""
    
    def __init__(self, max_history: int = config.MAX_CONVERSATION_HISTORY):
        self.max_history = max_history
        self.conversation_history: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: str, agent: str = None):
        """Add a message to conversation history."""
        message = {
            'role': role,
            'content': content,
            'agent': agent,
            'timestamp': asyncio.get_event_loop().time()
        }
        self.conversation_history.append(message)
        
        # Trim history if too long
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def get_optimized_history(self) -> List[Dict[str, Any]]:
        """Get optimized conversation history."""
        return self.conversation_history.copy()
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
    
    def get_summary(self) -> str:
        """Get a summary of the conversation for context."""
        if not self.conversation_history:
            return "New conversation"
        
        # Get key information from recent messages
        recent_messages = self.conversation_history[-3:]  # Last 3 messages
        summary_parts = []
        
        for msg in recent_messages:
            if msg['role'] == 'user':
                summary_parts.append(f"User: {msg['content'][:100]}...")
            elif msg['role'] == 'assistant':
                summary_parts.append(f"Assistant: {msg['content'][:100]}...")
        
        return " | ".join(summary_parts)

# Global context manager
context_manager = ContextManager()
