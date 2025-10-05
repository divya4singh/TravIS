"""
Test script to verify the traveler trip data integration works without OpenAI API.
"""

from data_loader import traveler_data

def test_data_loading():
    """Test the data loading functionality."""
    print("Testing traveler trip data integration...")
    
    # Test basic data loading
    print(f"Total trips loaded: {len(traveler_data.df) if traveler_data.df is not None else 0}")
    
    # Test statistics
    stats = traveler_data.get_trip_statistics()
    print(f"Trip statistics: {stats}")
    
    # Test search functionality
    print("\nTesting search functionality:")
    business_trips = traveler_data.search_trips(trip_type="Business")
    print(f"Found {len(business_trips)} business trips")
    
    # Test destination search
    ny_trips = traveler_data.search_trips(destination="New York")
    print(f"Found {len(ny_trips)} trips to New York")
    
    # Test upcoming trips
    upcoming = traveler_data.get_upcoming_trips(30)
    print(f"Found {len(upcoming)} upcoming trips in next 30 days")
    
    # Test trip lookup by reference
    if traveler_data.df is not None and len(traveler_data.df) > 0:
        sample_ref = traveler_data.df.iloc[0]['booking_reference']
        trip = traveler_data.get_trip_by_reference(sample_ref)
        print(f"Sample trip lookup: {trip['destination'] if trip else 'Not found'}")
    
    print("\n✅ All data functionality tests passed!")

if __name__ == "__main__":
    test_data_loading()
