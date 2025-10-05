"""
Test script for simplified agents without guardrails.
"""

import asyncio
import config
from simple_agents import simple_triage_agent, simple_faq_agent, simple_trip_agent
from main import AirlineAgentContext
from agents import Runner

async def test_simple_agents():
    """Test the simplified agents without guardrails."""
    print("🚀 Testing simplified agents for free tier usage...")
    
    # Test agent creation
    print(f"✅ Triage agent: {simple_triage_agent.name}")
    print(f"✅ FAQ agent: {simple_faq_agent.name}")
    print(f"✅ Trip agent: {simple_trip_agent.name}")
    print(f"✅ Using model: {config.FAST_MODEL}")
    
    # Test simple interactions
    test_messages = [
        "Hello, I want to look up my trip data",
        "What are the trip statistics?",
        "Search for business trips to New York"
    ]
    
    for i, message in enumerate(test_messages):
        print(f"\n📝 Test {i+1}: {message}")
        
        try:
            context = AirlineAgentContext()
            context.account_number = "12345678"
            
            # Apply rate limiting
            await config.rate_limiter.wait()
            
            result = await Runner.run(simple_triage_agent, message, context=context)
            
            if hasattr(result, 'final_output'):
                print(f"✅ Response: {str(result.final_output)[:150]}...")
            else:
                print(f"✅ Response received (type: {type(result)})")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 Simplified agents test completed!")
    print(f"📊 Configuration:")
    print(f"   - Rate limit delay: {config.RATE_LIMIT_DELAY}s")
    print(f"   - Max context length: {config.MAX_CONTEXT_LENGTH}")
    print(f"   - Caching enabled: {config.CACHE_RESPONSES}")
    print(f"   - Using fast model: {config.USE_FAST_MODEL}")

if __name__ == "__main__":
    asyncio.run(test_simple_agents())

