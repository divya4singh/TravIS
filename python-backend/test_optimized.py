"""
Test script for optimized agents with rate limiting and caching.
"""

import asyncio
import config
from main import triage_agent, traveler_data
from optimized_agents import create_optimized_agent, context_manager

async def test_optimized_agents():
    """Test the optimized agents with rate limiting and caching."""
    print("🚀 Testing optimized agents for free tier usage...")
    
    # Test data loading
    print(f"✅ Data loaded: {len(traveler_data.df)} trips")
    
    # Test optimized agent creation
    optimized_agent = create_optimized_agent(triage_agent, use_fast_model=True)
    print(f"✅ Optimized agent created: {optimized_agent.agent.name}")
    print(f"✅ Using model: {optimized_agent.model}")
    
    # Test context management
    context_manager.add_message("user", "Hello, I want to look up my trip data")
    print(f"✅ Context manager: {len(context_manager.conversation_history)} messages")
    
    # Test rate limiting
    print("⏱️  Testing rate limiting...")
    start_time = asyncio.get_event_loop().time()
    
    # Test multiple requests with rate limiting
    test_messages = [
        "Hello, I want to look up my trip data",
        "What are the trip statistics?",
        "Search for business trips to New York"
    ]
    
    for i, message in enumerate(test_messages):
        print(f"📝 Test {i+1}: {message}")
        
        try:
            # Import the context class directly
            from main import AirlineAgentContext
            context = AirlineAgentContext()
            context.account_number = "12345678"
            
            result = await optimized_agent.run_with_optimization(
                message, 
                context=context
            )
            
            if hasattr(result, 'final_output'):
                print(f"✅ Response: {str(result.final_output)[:100]}...")
            else:
                print(f"✅ Response received (type: {type(result)})")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    end_time = asyncio.get_event_loop().time()
    total_time = end_time - start_time
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    
    # Test caching
    print("💾 Testing caching...")
    cache_key = "test_cache_key"
    test_response = "This is a test response"
    
    config.cache_response(cache_key, test_response)
    cached_response = config.get_cached_response(cache_key)
    
    if cached_response == test_response:
        print("✅ Caching works correctly")
    else:
        print("❌ Caching failed")
    
    print("\n🎉 All optimization tests completed!")
    print(f"📊 Configuration:")
    print(f"   - Rate limit delay: {config.RATE_LIMIT_DELAY}s")
    print(f"   - Max context length: {config.MAX_CONTEXT_LENGTH}")
    print(f"   - Max conversation history: {config.MAX_CONVERSATION_HISTORY}")
    print(f"   - Caching enabled: {config.CACHE_RESPONSES}")
    print(f"   - Using fast model: {config.USE_FAST_MODEL}")

if __name__ == "__main__":
    asyncio.run(test_optimized_agents())
