"""
Data loader module for traveler trip data.
This module handles loading and processing of traveler trip dataset.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import os

class TravelerTripData:
    """Class to handle traveler trip data operations."""
    
    def __init__(self, data_path: Optional[str] = None):
        """Initialize the data loader."""
        self.data_path = data_path
        self.df: Optional[pd.DataFrame] = None
        self.load_data()
    
# Function to load data from the specific CSV file
    def load_data_from_csv(self):
        """Load data from the Travel_Details_Dataset.csv file."""
        csv_path = r"C:\Users\I332248\Documents\Github\openai-cs-agents-demo\python-backend\dataset\Travel_Details_Dataset.csv"
        self.df = pd.read_csv(csv_path)
        print(f"Loaded CSV data from {csv_path} with {len(self.df)} records")
        return self.df



    def load_data_1(self):
        """Load traveler trip data from CSV or create sample data."""
        if self.data_path and os.path.exists(self.data_path):
            try:
                self.df = pd.read_csv(self.data_path)
                print(f"Loaded data from {self.data_path}")
            except Exception as e:
                print(f"Error loading data from {self.data_path}: {e}")
                self._create_sample_data()
        else:
            print("No data file found, creating sample data...")
            self._create_sample_data()
    
    def load_data(self):
        """Load traveler trip data from a specific CSV file and map columns to match expected structure."""
        try:
            # Read the CSV file
            csv_df = self.load_data_from_csv()
            print(f"Loaded CSV data with {len(csv_df)} records")
            
            # Helper function to clean cost values
            def clean_cost(value):
                """Clean cost values by removing $, commas, USD, and spaces, then convert to int."""
                if pd.isna(value):
                    return 0
                # Convert to string, remove $, commas, USD, and strip whitespace
                cleaned = str(value).replace('$', '').replace(',', '').replace('USD', '').strip()
                try:
                    return int(cleaned) if cleaned else 0
                except ValueError:
                    print(f"Warning: Could not parse cost value '{value}', using 0")
                    return 0
            
            # Map CSV columns to our expected structure
            # The CSV has: Trip ID, Destination, Start date, End date, Duration (days), 
            # Traveler name, Traveler age, Traveler gender, Traveler nationality, 
            # Accommodation type, Accommodation cost, Transportation type, Transportation cost
            
            # Clean the cost columns
            accommodation_costs = csv_df['Accommodation cost'].apply(clean_cost)
            transportation_costs = csv_df['Transportation cost'].apply(clean_cost)
            
            mapped_data = {
                'trip_id': csv_df['Trip ID'].astype(str).apply(lambda x: f"TRP-{x.zfill(6)}"),
                'traveler_name': csv_df['Traveler name'],
                'destination': csv_df['Destination'],
                'trip_type': 'Leisure',  # Default since CSV doesn't have this field
                'start_date': pd.to_datetime(csv_df['Start date']).dt.strftime('%Y-%m-%d'),
                'end_date': pd.to_datetime(csv_df['End date']).dt.strftime('%Y-%m-%d'),
                'duration_days': csv_df['Duration (days)'],
                'budget': accommodation_costs + transportation_costs,
                'accommodation_type': csv_df['Accommodation type'],
                'transportation': csv_df['Transportation type'],
                'group_size': 1,  # Default since CSV doesn't have this field
                'rating': 4.5,  # Default rating since CSV doesn't have this field
                'status': pd.to_datetime(csv_df['End date']).apply(
                    lambda x: 'Completed' if x <= pd.to_datetime('2021-01-01') else 'Upcoming'
                ),
                'booking_reference': csv_df['Trip ID'].astype(str).apply(
                    lambda x: f"BK-{x.zfill(8)}"
                ),
                'flight_number': csv_df['Trip ID'].astype(str).apply(
                    lambda x: f"FLT-{int(x) % 900 + 100}"
                ),
                'seat_preference': 'Window',  # Default since CSV doesn't have this field
                'special_requests': 'None',  # Default since CSV doesn't have this field
                # Additional fields from CSV
                'traveler_age': csv_df['Traveler age'],
                'traveler_gender': csv_df['Traveler gender'],
                'traveler_nationality': csv_df['Traveler nationality'],
                'accommodation_cost': accommodation_costs,
                'transportation_cost': transportation_costs
            }
            
            # Create DataFrame with mapped data
            self.df = pd.DataFrame(mapped_data)
            #print df
            #show 5 rows all columns as table with index
            pd.set_option('display.max_rows', 5)
            pd.set_option('display.max_columns', 22)
            print(self.df.to_string(index=False))
            print(f"Successfully mapped and loaded {len(self.df)} trips from CSV")
            
        except Exception as e:
            print(f"Error loading data from CSV: {e}")
            print("Falling back to sample data...")
            self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample traveler trip data for demonstration."""
        np.random.seed(42)
        random.seed(42)
        
        # Sample data based on typical traveler trip dataset structure
        n_trips = 1000
        
        # Generate sample data
        data = {
            'trip_id': [f"TRP-{i:06d}" for i in range(1, n_trips + 1)],
            'traveler_name': [f"Traveler_{i}" for i in range(1, n_trips + 1)],
            'destination': np.random.choice([
                'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 
                'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose',
                'London', 'Paris', 'Tokyo', 'Sydney', 'Toronto', 'Berlin', 'Rome'
            ], n_trips),
            'trip_type': np.random.choice(['Business', 'Leisure', 'Family', 'Solo'], n_trips),
            'start_date': [
                (datetime.now() + timedelta(days=random.randint(-365, 365))).strftime('%Y-%m-%d')
                for _ in range(n_trips)
            ],
            'end_date': [
                (datetime.now() + timedelta(days=random.randint(-365, 365) + random.randint(1, 14))).strftime('%Y-%m-%d')
                for _ in range(n_trips)
            ],
            'duration_days': np.random.randint(1, 15, n_trips),
            'budget': np.random.randint(500, 5000, n_trips),
            'accommodation_type': np.random.choice(['Hotel', 'Airbnb', 'Hostel', 'Resort', 'Apartment'], n_trips),
            'transportation': np.random.choice(['Flight', 'Train', 'Car', 'Bus', 'Cruise'], n_trips),
            'group_size': np.random.randint(1, 8, n_trips),
            'rating': np.round(np.random.uniform(3.0, 5.0, n_trips), 1),
            'status': np.random.choice(['Completed', 'Upcoming', 'Cancelled', 'In Progress'], n_trips),
            'booking_reference': [f"BK-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))}" for _ in range(n_trips)],
            'flight_number': [f"FLT-{random.randint(100, 999)}" for _ in range(n_trips)],
            'seat_preference': np.random.choice(['Window', 'Aisle', 'Middle', 'Exit Row'], n_trips),
            'special_requests': np.random.choice([
                'Vegetarian Meal', 'Wheelchair Access', 'Extra Legroom', 'Pet Travel', 
                'None', 'Early Check-in', 'Late Check-out'
            ], n_trips)
        }
        
        self.df = pd.DataFrame(data)
        print(f"Created sample data with {len(self.df)} trips")
    
    def get_trip_by_reference(self, booking_reference: str) -> Optional[Dict[str, Any]]:
        """Get trip details by booking reference."""
        if self.df is None:
            return None
        
        trip = self.df[self.df['booking_reference'] == booking_reference]
        if trip.empty:
            return None
        
        return trip.iloc[0].to_dict()
    
    def get_trips_by_traveler(self, traveler_name: str) -> List[Dict[str, Any]]:
        """Get all trips for a specific traveler."""
        if self.df is None:
            return []
        
        trips = self.df[self.df['traveler_name'] == traveler_name]
        return trips.to_dict('records')
    
    def get_upcoming_trips(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming trips within specified days."""
        if self.df is None:
            return []
        
        current_date = datetime.now()
        future_date = current_date + timedelta(days=days_ahead)
        
        # Convert string dates to datetime for comparison
        self.df['start_date_dt'] = pd.to_datetime(self.df['start_date'])
        
        upcoming = self.df[
            (self.df['start_date_dt'] >= current_date) & 
            (self.df['start_date_dt'] <= future_date) &
            (self.df['status'] == 'Upcoming')
        ]
        
        return upcoming.to_dict('records')
    
    def search_trips(self, destination: Optional[str] = None, 
                    trip_type: Optional[str] = None,
                    min_budget: Optional[int] = None,
                    max_budget: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search trips based on criteria."""
        if self.df is None:
            return []
        
        filtered_df = self.df.copy()
        
        if destination:
            filtered_df = filtered_df[filtered_df['destination'].str.contains(destination, case=False, na=False)]
        
        if trip_type:
            filtered_df = filtered_df[filtered_df['trip_type'] == trip_type]
        
        if min_budget is not None:
            filtered_df = filtered_df[filtered_df['budget'] >= min_budget]
        
        if max_budget is not None:
            filtered_df = filtered_df[filtered_df['budget'] <= max_budget]
        
        return filtered_df.to_dict('records')
    
    def get_trip_statistics(self) -> Dict[str, Any]:
        """Get overall trip statistics."""
        if self.df is None:
            return {}
        
        return {
            'total_trips': len(self.df),
            'completed_trips': len(self.df[self.df['status'] == 'Completed']),
            'upcoming_trips': len(self.df[self.df['status'] == 'Upcoming']),
            'cancelled_trips': len(self.df[self.df['status'] == 'Cancelled']),
            'average_rating': round(self.df['rating'].mean(), 2),
            'average_budget': round(self.df['budget'].mean(), 2),
            'most_popular_destination': self.df['destination'].mode().iloc[0] if not self.df['destination'].mode().empty else 'N/A',
            'most_common_trip_type': self.df['trip_type'].mode().iloc[0] if not self.df['trip_type'].mode().empty else 'N/A'
        }
    
    def get_destinations(self) -> List[str]:
        """Get list of all unique destinations."""
        if self.df is None:
            return []
        return sorted(self.df['destination'].unique().tolist())
    
    def get_trip_types(self) -> List[str]:
        """Get list of all unique trip types."""
        if self.df is None:
            return []
        return sorted(self.df['trip_type'].unique().tolist())


    #check if trip is eligible for cancellation
    def cancel_upcoming_trip_or_booking(self, ref: str) -> bool:
        """Cancel an upcoming trip by booking reference or trip id. Sets status to 'CANCELLED' and makes the trip immutable."""
        if self.df is None:
            return False
        # Find by booking_reference or trip_id
        trip = self.get_trip_by_reference(ref)
        # Only allow cancellation if status is 'Upcoming' and not already cancelled/immutable
        if trip is None:
            return False
        is_eligible_for_cancellation = trip['status'] == 'Upcoming'
        if not is_eligible_for_cancellation:
            return False  # Not upcoming or already cancelled
        # Set status to 'CANCELLED' and mark as immutable
        trip['status'] = 'CANCELLED'
        return True
    # def cancel_upcoming_trip_or_booking(self, ref: str) -> bool:
    #     """Cancel an upcoming trip by booking reference or trip id. Sets status to 'CANCELLED' and makes the trip immutable."""
    #     if self.df is None:
    #         return False

    #     # Ensure 'immutable' column exists
    #     if 'immutable' not in self.df.columns:
    #         self.df['immutable'] = False

    #     # Find matching rows that are Upcoming and not already immutable
    #     mask = (
    #         ((self.df['booking_reference'] == ref) | (self.df['trip_id'] == ref)) &
    #         (self.df['status'] == 'Upcoming') &
    #         (~self.df['immutable'])
    #     )
    #     if not mask.any():
    #         return False

    #     # Update status and set immutable
    #     self.df.loc[mask, 'status'] = 'CANCELLED'
    #     self.df.loc[mask, 'immutable'] = True
    #     return True

# Global instance
traveler_data = TravelerTripData()

