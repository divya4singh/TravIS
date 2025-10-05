#!/usr/bin/env python3
"""
Test script to verify CSV data loading functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_data_from_csv, traveler_data

def test_csv_loading():
    """Test the CSV loading functionality."""
    print("Testing CSV data loading...")
    
    # Load data from CSV
    load_data_from_csv()
    
    # Test basic functionality
    print(f"\nLoaded {len(traveler_data.df)} trips from CSV")
    
    # Test getting a trip by reference
    if len(traveler_data.df) > 0:
        first_trip_ref = traveler_data.df.iloc[0]['booking_reference']
        trip = traveler_data.get_trip_by_reference(first_trip_ref)
        if trip:
            print(f"\nSample trip by reference '{first_trip_ref}':")
            print(f"  Traveler: {trip['traveler_name']}")
            print(f"  Destination: {trip['destination']}")
            print(f"  Duration: {trip['duration_days']} days")
            print(f"  Budget: ${trip['budget']}")
            print(f"  Accommodation: {trip['accommodation_type']}")
            print(f"  Transportation: {trip['transportation']}")
    
    # Test getting trips by traveler
    if len(traveler_data.df) > 0:
        first_traveler = traveler_data.df.iloc[0]['traveler_name']
        trips = traveler_data.get_trips_by_traveler(first_traveler)
        print(f"\nTrips for traveler '{first_traveler}': {len(trips)} trips")
    
    # Test search functionality
    search_results = traveler_data.search_trips(destination="London")
    print(f"\nTrips to London: {len(search_results)} trips")
    
    # Test statistics
    stats = traveler_data.get_trip_statistics()
    print(f"\nTrip Statistics:")
    print(f"  Total trips: {stats.get('total_trips', 0)}")
    print(f"  Average budget: ${stats.get('average_budget', 0)}")
    print(f"  Most popular destination: {stats.get('most_popular_destination', 'N/A')}")
    
    # Show column information
    print(f"\nDataFrame columns: {list(traveler_data.df.columns)}")
    print(f"DataFrame shape: {traveler_data.df.shape}")
    
    print("\nCSV loading test completed successfully!")

if __name__ == "__main__":
    test_csv_loading()
