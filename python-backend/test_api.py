"""
Test script to verify the API works with OpenAI integration.
"""

import config
from main import triage_agent, traveler_data
from agents import Runner

async def test_agent_functionality():
    """Test that the agents can work with the OpenAI API."""
    print("Testing agent functionality with OpenAI API...")
    
    # Test data loading
    print(f"✅ Data loaded: {len(traveler_data.df)} trips")
    
    # Test agent creation
    print(f"✅ Triage agent created: {triage_agent.name}")
    print(f"✅ Agent has {len(triage_agent.tools)} tools")
    
    # Test a simple agent interaction
    try:
        context = triage_agent.context_type()
        context.account_number = "12345678"
        
        result = await Runner.run(triage_agent, "Hello, I want to look up my trip data", context=context)
        print("✅ Agent interaction successful!")
        print(f"Response: {result.final_output}")
        
    except Exception as e:
        print(f"❌ Agent interaction failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_agent_functionality())
    if success:
        print("\n🎉 All tests passed! The project is ready to run.")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
