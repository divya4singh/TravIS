#!/usr/bin/env python3
"""
Test script to verify cost parsing functionality.
"""

import pandas as pd

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

# Test cases from the CSV
test_values = [
    "1200",  # Normal case
    "$900 ",  # With dollar sign and space
    "$1,500 ",  # With dollar sign, comma, and space
    "$1,200 ",  # With dollar sign, comma, and space
    "$400 ",  # With dollar sign and space
    "600",  # Normal case
    "$800 ",  # With dollar sign and space
    "$1,000 ",  # With dollar sign, comma, and space
    "$1,400 ",  # With dollar sign, comma, and space
    "$2,000 ",  # With dollar sign, comma, and space
    "$1,100 ",  # With dollar sign, comma, and space
    "$1,500 ",  # With dollar sign, comma, and space
    "$1,200 ",  # With dollar sign, comma, and space
    "500 USD",  # With USD
    "1000 USD",  # With USD
    "800 USD",  # With USD
    "1500 USD",  # With USD
]

print("Testing cost parsing:")
for value in test_values:
    cleaned = clean_cost(value)
    print(f"'{value}' -> {cleaned}")

print("\nTesting edge cases:")
edge_cases = ["", " ", "$", "abc", None]
for value in edge_cases:
    cleaned = clean_cost(value)
    print(f"'{value}' -> {cleaned}")
