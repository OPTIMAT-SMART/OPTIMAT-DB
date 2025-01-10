"""
Simple API Tests
---------------
Tests the OPTIMAT Backend API endpoints using direct HTTP requests.
"""

import httpx
import pytest
from datetime import datetime, timedelta
import json
from typing import Dict, Any
import random

# API Configuration
BASE_URL = "http://localhost:8000"  # Update with your server URL
ENDPOINT = "/api/match"  # Changed from "/api/transportation/providers/match"

# Add the addresses list
ADD = [
    "2151 Salvio St, Concord, CA 94520",
    "1601 Civic Dr, Walnut Creek, CA 94596",
    "100 Gregory Ln, Pleasant Hill, CA 94523",
    "525 Henrietta St, Martinez, CA 94553",
    "300 L St, Antioch, CA 94509",
    "150 City Park Way, Brentwood, CA 94513",
    "65 Civic Ave, Pittsburg, CA 94565",
    "3231 Main St, Oakley, CA 94561",
    "111 Civic Dr, Hercules, CA 94547",
    "2131 Pear St, Pinole, CA 94564",
    "3769 San Pablo Dam Rd, El Sobrante, CA 94803",
    "800 Willow Ave, Rodeo, CA 94572",
    "2180 Milvia St, Berkeley, CA 94704",
    "1 Frank H. Ogawa Plaza, Oakland, CA 94612",
    "450 Civic Center Plaza, Richmond, CA 94804",
    "10890 San Pablo Ave, El Cerrito, CA 94530",
    "1666 North Main St, Walnut Creek, CA 94596",
    "1950 Parkside Dr, Concord, CA 94519",
    "100 Gregory Ln, Pleasant Hill, CA 94523",
    "3675 Mt Diablo Blvd, Lafayette, CA 94549",
    "100 Civic Plaza, Dublin, CA 94568",
    "123 Main St, Pleasanton, CA 94566",
    "1052 S Livermore Ave, Livermore, CA 94550",
    "7000 Bollinger Canyon Rd, San Ramon, CA 94583",
    "13831 San Pablo Ave, San Pablo, CA 94806",
    "1666 San Pablo Ave, Berkeley, CA 94702",
    "1 Frank H. Ogawa Plaza, Oakland, CA 94612",
    "450 Civic Center Plaza, Richmond, CA 94804",
    "10890 San Pablo Ave, El Cerrito, CA 94530",
    "3231 Main St, Oakley, CA 94561",
    "65 Civic Ave, Pittsburg, CA 94565",
    "150 City Park Way, Brentwood, CA 94513",
    "300 L St, Antioch, CA 94509",
    "3231 Main St, Oakley, CA 94561",
    "65 Civic Ave, Pittsburg, CA 94565",
    "150 City Park Way, Brentwood, CA 94513",
    "300 L St, Antioch, CA 94509",
    "100 Civic Plaza, Dublin, CA 94568",
    "123 Main St, Pleasanton, CA 94566",
    "1052 S Livermore Ave, Livermore, CA 94550",
    "7000 Bollinger Canyon Rd, San Ramon, CA 94583",
    "1666 North Main St, Walnut Creek, CA 94596",
    "1950 Parkside Dr, Concord, CA 94519",
    "100 Gregory Ln, Pleasant Hill, CA 94523",
    "3675 Mt Diablo Blvd, Lafayette, CA 94549",
    "1 Frank H. Ogawa Plaza, Oakland, CA 94612",
    "2180 Milvia St, Berkeley, CA 94704",
    "450 Civic Center Plaza, Richmond, CA 94804",
    "10890 San Pablo Ave, El Cerrito, CA 94530",
    "2131 Pear St, Pinole, CA 94564",
    "111 Civic Dr, Hercules, CA 94547",
    "3769 San Pablo Dam Rd, El Sobrante, CA 94803",
    "800 Willow Ave, Rodeo, CA 94572",
    "2151 Salvio St, Concord, CA 94520",
    "1601 Civic Dr, Walnut Creek, CA 94596",
    "100 Gregory Ln, Pleasant Hill, CA 94523",
    "525 Henrietta St, Martinez, CA 94553",
    "300 L St, Antioch, CA 94509",
    "150 City Park Way, Brentwood, CA 94513",
    "65 Civic Ave, Pittsburg, CA 94565",
    "3231 Main St, Oakley, CA 94561",
    "111 Civic Dr, Hercules, CA 94547",
    "2131 Pear St, Pinole, CA 94564",
    "3769 San Pablo Dam Rd, El Sobrante, CA 94803",
    "800 Willow Ave, Rodeo, CA 94572",
    "2180 Milvia St, Berkeley, CA 94704",
    "1 Frank H. Ogawa Plaza, Oakland, CA 94612",
    "450 Civic Center Plaza, Richmond, CA 94804",
    "10890 San Pablo Ave, El Cerrito, CA 94530",
    "1666 North Main St, Walnut Creek, CA 94596",
    "1950 Parkside Dr, Concord, CA 94519",
    "100 Gregory Ln, Pleasant Hill, CA 94523",
    "3675 Mt Diablo Blvd, Lafayette, CA 94549",
    "100 Civic Plaza, Dublin, CA 94568",
    "123 Main St, Pleasanton, CA 94566",
    "1052 S Livermore Ave, Livermore, CA 94550",
    "7000 Bollinger Canyon Rd, San Ramon, CA 94583",
    "13831 San Pablo Ave, San Pablo, CA 94806",
    "1666 San Pablo Ave, Berkeley, CA 94702",
    "1 Frank H. Ogawa Plaza, Oakland, CA 94612",
    "450 Civic Center Plaza, Richmond, CA 94804",
    "10890 San Pablo Ave, El Cerrito, CA 94530",
    "3231 Main St, Oakley, CA 94561",
    "65 Civic Ave, Pittsburg, CA 94565",
    "150 City Park Way, Brentwood, CA 94513",
    "300 L St, Antioch, CA 94509",
    "3231 Main St, Oakley, CA 94561",
    "65 Civic Ave, Pittsburg, CA 94565",
    "150 City Park Way, Brentwood, CA 94513",
    "300 L St, Antioch, CA 94509",
    "100 Civic Plaza, Dublin, CA 94568",
    "123 Main St, Pleasanton, CA 94566",
    "1052 S Livermore Ave, Livermore, CA 94550",
    "7000 Bollinger Canyon Rd, San Ramon, CA 94583"
]
def format_json(data: Dict[str, Any]) -> str:
    """Format JSON data for readable output"""
    return json.dumps(data, indent=2)

def print_response_details(response) -> None:
    """Print detailed response information for debugging"""
    print("\n=== Response Details ===")
    print(f"Status Code: {response.status_code}")
    print("\nHeaders:")
    for key, value in response.headers.items():
        print(f"{key}: {value}")
    print("\nBody:")
    try:
        print(format_json(response.json()))
    except Exception:
        print(response.text)
    print("=====================")

@pytest.fixture
def valid_request():
    """Sample valid request data"""
    return {
        'departureTime': (datetime.now() + timedelta(hours=1)).isoformat(),
        'returnTime': (datetime.now() + timedelta(hours=2)).isoformat(),
        'originAddress': '123 Main St, City, State',
        'destinationAddress': '456 Oak Ave, City, State',
        'eligibility': ['senior', 'disability'],
        'equipment': ['wheelchair'],
        'healthConditions': ['none'],
        'needsCompanion': True,
        'allowsSharing': True
    }

@pytest.mark.asyncio
async def test_missing_fields():
    """Test request with missing required fields"""
    async with httpx.AsyncClient() as client:
        invalid_data = {
            'departureTime': datetime.now().isoformat()
            # Missing other fields
        }
        
        response = await client.post(f"{BASE_URL}{ENDPOINT}", json=invalid_data)
        
        try:
            assert response.status_code == 400, \
                f"Expected status code 400, got {response.status_code}"
            
            data = response.json()
            assert data['status'] == 'VALIDATION_ERROR', \
                f"Expected status 'VALIDATION_ERROR', got {data.get('status')}"
            assert 'error' in data, \
                f"Missing 'error' in response\n" \
                f"Response: {format_json(data)}"
        except AssertionError as e:
            print_response_details(response)
            raise

@pytest.mark.asyncio
async def test_invalid_date():
    """Test request with invalid date format"""
    async with httpx.AsyncClient() as client:
        invalid_data = {
            'departureTime': 'invalid-date',
            'returnTime': 'invalid-date',
            'originAddress': '123 Main St',
            'destinationAddress': '456 Oak Ave',
            'eligibility': ['senior'],
            'equipment': [],
            'healthConditions': ['none'],
            'needsCompanion': False,
            'allowsSharing': True
        }
        
        response = await client.post(f"{BASE_URL}{ENDPOINT}", json=invalid_data)
        
        try:
            assert response.status_code in [400, 500], \
                f"Expected status code 400 or 500, got {response.status_code}"
            
            data = response.json()
            assert 'status' in data, \
                f"Missing 'status' in response\n" \
                f"Response: {format_json(data)}"
            assert 'error' in data, \
                f"Missing 'error' in response\n" \
                f"Response: {format_json(data)}"
        except AssertionError as e:
            print_response_details(response)
            raise

@pytest.mark.asyncio
@pytest.mark.parametrize('field', [
    'departureTime',
    'returnTime',
    'originAddress',
    'destinationAddress',
    'eligibility',
    'equipment',
    'healthConditions',
    'needsCompanion',
    'allowsSharing'
])
async def test_missing_individual_fields(valid_request, field):
    """Test omitting each required field individually"""
    test_data = valid_request.copy()
    del test_data[field]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}{ENDPOINT}", json=test_data)
        
        try:
            assert response.status_code == 400, \
                f"Expected status code 400, got {response.status_code}"
            
            data = response.json()
            assert data['status'] == 'VALIDATION_ERROR', \
                f"Expected status 'VALIDATION_ERROR', got {data.get('status')}"
            assert 'error' in data, \
                f"Missing 'error' in response"
            assert field in data.get('error', ''), \
                f"Error message should mention missing field '{field}'\n" \
                f"Error message: {data.get('error')}"
        except AssertionError as e:
            print("\n=== Test Details ===")
            print(f"Testing missing field: {field}")
            print(f"Request data: {format_json(test_data)}")
            print_response_details(response)
            raise

@pytest.mark.asyncio
@pytest.mark.parametrize('_', range(10))  # Run 10 times with different random addresses
async def test_random_addresses_and_times(_):
    """Test provider matching with random addresses and times during the day"""
    # Select two different random addresses
    origin, destination = random.sample(ADDRESSES, 2)
    
    # Generate random times for today
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Generate departure time between 6 AM and 6 PM
    min_departure = today.replace(hour=6)  # 6 AM
    max_departure = today.replace(hour=18)  # 6 PM
    departure_minutes = random.randint(0, (max_departure - min_departure).seconds // 60)
    departure_time = min_departure + timedelta(minutes=departure_minutes)
    
    # Generate return time between departure time and 10 PM
    min_return = departure_time + timedelta(minutes=30)  # At least 30 minutes after departure
    max_return = today.replace(hour=22)  # 10 PM
    if min_return >= max_return:
        max_return = min_return + timedelta(hours=2)
    return_minutes = random.randint(0, (max_return - min_return).seconds // 60)
    return_time = min_return + timedelta(minutes=return_minutes)
    
    request_data = {
        'departureTime': departure_time.isoformat(),
        'returnTime': return_time.isoformat(),
        'originAddress': origin,
        'destinationAddress': destination,
        'eligibility': ['senior', 'disability'],
        'equipment': ['wheelchair'],
        'healthConditions': ['none'],
        'needsCompanion': True,
        'allowsSharing': True
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}{ENDPOINT}", json=request_data)
        
        try:
            assert response.status_code == 200, \
                f"Expected status code 200, got {response.status_code}\n" \
                f"Response: {format_json(response.json())}"
            
            data = response.json()
            assert isinstance(data, list), \
                f"Expected list response, got {type(data)}\n" \
                f"Response: {format_json(data)}"
            
            print(f"\nTested route from {origin} to {destination}")
            print(f"Departure: {departure_time.strftime('%I:%M %p')}")
            print(f"Return: {return_time.strftime('%I:%M %p')}")
            print(f"Found {len(data)} matching providers")
            
            if len(data) > 0:
                for provider in data:
                    assert isinstance(provider, dict), \
                        f"Expected dict provider, got {type(provider)}\n" \
                        f"Provider: {format_json(provider)}"
                    
                    for field in ['ID', 'Provider', 'Type']:
                        assert field in provider, \
                            f"Missing required field '{field}' in provider\n" \
                            f"Provider: {format_json(provider)}"
        except AssertionError as e:
            print("\n=== Test Details ===")
            print(f"Origin: {origin}")
            print(f"Destination: {destination}")
            print(f"Departure: {departure_time.strftime('%I:%M %p')}")
            print(f"Return: {return_time.strftime('%I:%M %p')}")
            print_response_details(response)
            raise

def pytest_configure(config):
    """Add markers to pytest configuration"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    ) 
