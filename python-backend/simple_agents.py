"""
Simplified agents for free tier OpenAI usage without guardrails.
Optimized for gpt-3.5-turbo compatibility.
"""

import config
from agents import Agent, function_tool, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from data_loader import traveler_data
from main import AirlineAgentContext
import hashlib

# =========================
# SIMPLIFIED TOOLS (without guardrails)
# =========================

#create a tool for all agents to find current date. current date should be hard coded to 01-01-2021
@function_tool(
    name_override="current_date_tool",
    description_override="Find current date."
)
async def current_date_tool() -> str:
    """Find current date."""
    return "01-01-2021"

#create a tool for all agents to find current time. current time should be hard coded to 12:00:00
@function_tool(
    name_override="current_time_tool",
    description_override="Find current time."
)
async def current_time_tool() -> str:
    """Find current time."""
    return "12:00:00"

@function_tool(
    name_override="cancel_upcoming_trip_or_booking",
    description_override="Cancel an upcoming trip or booking by booking reference or trip id."
)
async def cancel_upcoming_trip_or_booking(
    ref: str
) -> str:
    """Cancel an upcoming trip or booking by booking reference or trip id."""
    result = traveler_data.cancel_upcoming_trip_or_booking(ref)
    if result:
        return f"Trip or booking with reference '{ref}' has been cancelled and is now immutable."
    else:
        return f"No upcoming trip found with reference '{ref}', or it is already cancelled/immutable."


@function_tool(
    name_override="faq_lookup_tool", 
    description_override="Lookup frequently asked questions."
)
async def simple_faq_lookup_tool(question: str) -> str:
    """Lookup answers to frequently asked questions with caching."""
    # Check cache first
    cache_key = f"faq_{hashlib.md5(question.lower().encode()).hexdigest()}"
    cached_response = config.get_cached_response(cache_key)
    if cached_response:
        return cached_response
    
    # Apply rate limiting
    await config.rate_limiter.wait()
    
    q = question.lower()
    response = ""
    
    if "bag" in q or "baggage" in q:
        response = (
            "You are allowed to bring one bag on the plane. "
            "It must be under 50 pounds and 22 inches x 14 inches x 9 inches."
        )
    elif "seats" in q or "plane" in q:
        response = (
            "There are 120 seats on the plane. "
            "There are 22 business class seats and 98 economy seats. "
            "Exit rows are rows 4 and 16. "
            "Rows 5-8 are Economy Plus, with extra legroom."
        )
    elif "wifi" in q:
        response = "We have free wifi on the plane, join Airline-Wifi"
    else:
        response = "I'm sorry, I don't know the answer to that question."
    
    # Cache the response
    config.cache_response(cache_key, response)
    return response

@function_tool(
    name_override="lookup_trip_data",
    description_override="Look up trip information using booking reference or traveler name."
)
async def simple_lookup_trip_data(
    booking_reference: str = None,
    traveler_name: str = None
) -> str:
    """Look up trip data using booking reference or traveler name with caching."""
    # Create cache key
    cache_key = f"trip_lookup_{booking_reference or traveler_name or 'none'}"
    cached_response = config.get_cached_response(cache_key)
    if cached_response:
        return cached_response
    
    # Apply rate limiting
    await config.rate_limiter.wait()
    
    response = ""
    
    if booking_reference:
        trip_data = traveler_data.get_trip_by_reference(booking_reference)
        if trip_data:
            response = f"Found trip data for booking reference {booking_reference}: \
            Destination: {trip_data.get('destination')}, \
            Trip Type: {trip_data.get('trip_type')}, Status: {trip_data.get('status')}, \
                Over All Information: {trip_data.items()}"
        else:
            response = f"No trip found for booking reference {booking_reference}"
    
    elif traveler_name:
        trips = traveler_data.get_trips_by_traveler(traveler_name)
        if trips:
            trip_summary = f"Found {len(trips)} trips for {traveler_name}:\n"
            for trip in trips[:5]:  # Show first 5 trips
                trip_summary += f"- {trip.get('destination')} ({trip.get('start_date')}) - {trip.get('status')}\n"
            if len(trips) > 5:
                trip_summary += f"... and {len(trips) - 5} more trips"
            response = trip_summary
        else:
            response = f"No trips found for traveler {traveler_name}"
    
    else:
        response = "Please provide either a booking reference or traveler name to look up trip data."
    
    # Cache the response
    config.cache_response(cache_key, response)
    return response

@function_tool(
    name_override="get_trip_statistics",
    description_override="Get overall trip statistics and insights."
)
async def simple_get_trip_statistics() -> str:
    """Get overall trip statistics."""
    cache_key = "trip_statistics"
    cached_response = config.get_cached_response(cache_key)
    if cached_response:
        return cached_response
    
    await config.rate_limiter.wait()
    
    stats = traveler_data.get_trip_statistics()
    response = f"""Trip Statistics:
- Total Trips: {stats.get('total_trips', 0)}
- Completed Trips: {stats.get('completed_trips', 0)}
- Upcoming Trips: {stats.get('upcoming_trips', 0)}
- Average Rating: {stats.get('average_rating', 0)}
- Average Budget: ${stats.get('average_budget', 0)}
- Most Popular Destination: {stats.get('most_popular_destination', 'N/A')}
- Most Common Trip Type: {stats.get('most_common_trip_type', 'N/A')}"""
    
    config.cache_response(cache_key, response)
    return response

@function_tool(
    name_override="search_trips",
    description_override="Search for trips based on destination, trip type, or budget range."
)
async def simple_search_trips(
    destination: str = None,
    trip_type: str = None,
    min_budget: int = None,
    max_budget: int = None
) -> str:
    """Search for trips based on criteria."""
    cache_key = f"search_{destination}_{trip_type}_{min_budget}_{max_budget}"
    cached_response = config.get_cached_response(cache_key)
    if cached_response:
        return cached_response
    
    await config.rate_limiter.wait()
    
    trips = traveler_data.search_trips(destination, trip_type, min_budget, max_budget)
    
    if not trips:
        response = "No trips found matching your criteria."
    else:
        response = f"Found {len(trips)} trips matching your criteria:\n"
        for trip in trips[:10]:  # Show first 10 results
            response += f"- {trip.get('destination')} ({trip.get('trip_type')}) - ${trip.get('budget')} - {trip.get('start_date')}\n"
        
        if len(trips) > 10:
            response += f"... and {len(trips) - 10} more trips"
    
    config.cache_response(cache_key, response)
    return response

# =========================
# SIMPLIFIED AGENTS (without guardrails)
# =========================

# Simple FAQ Agent
simple_faq_agent = Agent[AirlineAgentContext](
    name="FAQ Agent",
    model=config.FAST_MODEL,
    handoff_description="A helpful agent that can answer questions about the airline.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are an FAQ agent. Answer customer questions about airline services.
    Use the faq_lookup_tool to get accurate information.
    Keep responses concise and helpful.""",
    tools=[simple_faq_lookup_tool, current_date_tool, current_time_tool],
)

# Simple Trip Management Agent
simple_trip_agent = Agent[AirlineAgentContext](
    name="Trip Management Agent",
    model=config.FAST_MODEL,
    handoff_description="An agent that can help with trip data lookup and management like CRUD operations.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a Trip Management Agent. Help customers with:
    1. Looking up trip information using booking reference or traveler name
    2. Searching for trips by destination, type, or budget
    3. Getting trip statistics and insights
    4. Cancel Upcoming Trips
    Use the appropriate tools to help customers with their trip-related inquiries.""",
    tools=[simple_lookup_trip_data, simple_get_trip_statistics, simple_search_trips, current_date_tool, current_time_tool, cancel_upcoming_trip_or_booking],
)

# Simple Triage Agent
simple_triage_agent = Agent[AirlineAgentContext](
    name="Triage Agent",
    model=config.FAST_MODEL,
    handoff_description="A triage agent that can help with various airline services.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a helpful triage agent. You can help customers with:
    1. Trip data lookup and management
    2. Frequently asked questions
    3. General airline information
    Use the available tools to provide helpful responses.
    Keep responses concise and friendly.""",
    tools=[simple_lookup_trip_data, simple_get_trip_statistics, simple_search_trips, simple_faq_lookup_tool],
    handoffs=[simple_faq_agent, simple_trip_agent, current_date_tool, current_time_tool],
)

# Set up handoff relationships
simple_faq_agent.handoffs.append(simple_triage_agent)
simple_trip_agent.handoffs.append(simple_triage_agent)
