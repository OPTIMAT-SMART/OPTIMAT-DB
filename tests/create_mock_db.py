"""
Create Mock Database
------------------
Script to create and populate mock database tables for testing.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import random
import json
from src.utils.config import config

# Sample phone numbers
PHONE_NUMBERS = [
    "(925)938-7433",
    "(510)555-1234",
    "(415)777-8888",
    "(650)123-4567",
    "(408)999-0000",
    "(707)333-4444",
    "(831)222-5555",
    "(916)444-6666",
    "(209)888-9999",
    "(530)777-1111"
]

def load_geojson(file_path):
    """Load and return GeoJSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading GeoJSON file: {str(e)}")
        raise

def create_mock_table(cur):
    """Create the mock providers table if it doesn't exist"""
    try:
        # Drop the mock table if it exists
        cur.execute("""
            DROP TABLE IF EXISTS atccc.providers_mock CASCADE;
        """)
        
        # Create the mock table by copying the structure
        cur.execute("""
            CREATE TABLE atccc.providers_mock (LIKE atccc.providers INCLUDING ALL);
        """)
        
        print("✓ Mock table created successfully")
        
    except Exception as e:
        print(f"✗ Error creating mock table: {str(e)}")
        raise

def copy_provider_data(cur):
    """Copy all data from providers to providers_mock"""
    try:
        # Copy data
        cur.execute("""
            INSERT INTO atccc.providers_mock 
            SELECT * FROM atccc.providers;
        """)
        
        # Update null schedule_type with proper enum casting
        cur.execute("""
            UPDATE atccc.providers_mock 
            SET schedule_type = (
                CASE 
                    WHEN random() < 0.5 THEN 'fixed-schedules'::atccc.providers_schedule_type
                    ELSE 'in-advance-book'::atccc.providers_schedule_type
                END
            )
            WHERE schedule_type IS NULL;
        """)
        
        # Update null eligibility_req
        cur.execute("""
            UPDATE atccc.providers_mock 
            SET eligibility_req = (
                CASE 
                    WHEN random() < 0.5 THEN 'anonymous'::atccc.providers_eligibility_req
                    ELSE 'ada-approved'::atccc.providers_eligibility_req
                END
            )
            WHERE eligibility_req IS NULL;
        """)
        
        # Update booking with random phone numbers
        phone_numbers_json = json.dumps(PHONE_NUMBERS)
        cur.execute(f"""
            UPDATE atccc.providers_mock 
            SET booking = json_build_object(
                'call', (SELECT json_array_elements_text('{phone_numbers_json}'::json) 
                        OFFSET floor(random() * json_array_length('{phone_numbers_json}'::json))
                        LIMIT 1),
                'method', 'call center'
            )
            WHERE booking IS NULL OR booking->>'method' IS NULL;
        """)
        
        # Update fare types
        cur.execute("""
            UPDATE atccc.providers_mock 
            SET fare = CASE 
                WHEN random() < 0.5 THEN 
                    json_build_object('type', 'fixed')
                ELSE 
                    json_build_object('type', 'variable')
            END
            WHERE fare IS NULL OR fare->>'type' IS NULL;
        """)
        
        # Update service_hours
        cur.execute("""
            UPDATE atccc.providers_mock 
            SET service_hours = NULL
            WHERE service_hours IS NOT NULL AND random() < 0.3;
        """)
        
        cur.execute("""
            SELECT provider_id 
            FROM atccc.providers_mock 
            WHERE service_hours IS NULL;
        """)
        
        providers_to_update = cur.fetchall()
        for provider in providers_to_update:
            random_hours = generate_random_service_hours()
            cur.execute("""
                UPDATE atccc.providers_mock 
                SET service_hours = %s
                WHERE provider_id = %s;
            """, (json.dumps(random_hours), provider['provider_id']))
        
        print("✓ Updated service hours")
        
        # Update service_zones from provider-specific GeoJSON files
        try:
            output_dir = 'tests/service_zones/zones2'
            
            # Get providers with null service_zones
            cur.execute("""
                SELECT provider_id, provider_name 
                FROM atccc.providers_mock 
                WHERE service_zone IS NULL;
            """)
            
            providers = cur.fetchall()
            for provider in providers:
                service_name = provider['provider_name']
                file_path = os.path.join(output_dir, f"{service_name.replace(' ', '_')}.geojson")
                
                try:
                    geojson_data = load_geojson(file_path)
                    cur.execute("""
                        UPDATE atccc.providers_mock 
                        SET service_zone = %s::jsonb
                        WHERE provider_id = %s;
                    """, (json.dumps(geojson_data), provider['provider_id']))
                    print(f"✓ Updated service_zone for {service_name}")
                except FileNotFoundError:
                    print(f"⚠ No GeoJSON file found for {service_name}")
                    continue
                except Exception as e:
                    print(f"✗ Error processing {service_name}: {str(e)}")
                    continue
            
            print("✓ Completed service_zone updates")
        except Exception as e:
            print(f"✗ Error updating service_zones: {str(e)}")
            raise
        
        # Update planning_type randomly
        cur.execute("""
            UPDATE atccc.providers_mock 
            SET planning_type = (
                CASE 
                    WHEN random() < 0.33 THEN 'website'
                    WHEN random() < 0.66 THEN 'call'
                    ELSE 'app'
                END
            )
            WHERE planning_type IS NULL OR planning_type = '';
        """)
        
        # Update website using service name
        cur.execute("""
            UPDATE atccc.providers_mock 
            SET website = LOWER(CONCAT(REPLACE(provider_name, ' ', ''), '.com'))
            WHERE website IS NULL OR website = '';
        """)
        
        # Update contacts with default message
        cur.execute("""
            UPDATE atccc.providers_mock 
            SET contacts = 'no contact available'
            WHERE contacts IS NULL OR contacts = '';
        """)
        
        # Update contact_emails using service name
        cur.execute("""
            UPDATE atccc.providers_mock 
            SET contact_emails = LOWER(CONCAT(REPLACE(provider_name, ' ', ''), '@transport.org'))
            WHERE contact_emails IS NULL OR contact_emails = '';
        """)
        
        # Update provider_org with default value
        cur.execute("""
            UPDATE atccc.providers_mock 
            SET provider_org = 'government'
            WHERE provider_org IS NULL OR provider_org = '';
        """)
        
        print("✓ Updated provider details (planning_type, website, contacts, emails, org)")
        
        # Verify the copy
        cur.execute("SELECT COUNT(*) as count FROM atccc.providers")
        original_count = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM atccc.providers_mock")
        mock_count = cur.fetchone()['count']
        
        if original_count == mock_count:
            print(f"✓ Copied and updated {mock_count} rows successfully")
        else:
            raise Exception(f"Row count mismatch: {original_count} vs {mock_count}")
            
        # Print sample of updates
        cur.execute("""
            SELECT 
                provider_id,
                schedule_type::text,
                eligibility_req::text,
                booking->>'call' as phone,
                fare->>'type' as fare_type
            FROM atccc.providers_mock
            LIMIT 5;
        """)
        
        print("\nSample of updated records:")
        print("---------------------------")
        for row in cur.fetchall():
            print(f"Provider {row['provider_id']}:")
            print(f"  Schedule: {row['schedule_type']}")
            print(f"  Eligibility: {row['eligibility_req']}")
            print(f"  Phone: {row['phone']}")
            print(f"  Fare Type: {row['fare_type']}")
            print("---------------------------")
            
    except Exception as e:
        print(f"✗ Error copying/updating data: {str(e)}")
        raise

def generate_random_service_hours():
    """Generate random service hours in the required format"""
    num_schedules = 1
    hours = []
    
    for _ in range(num_schedules):
        # Generate random binary string for days (1=open, 0=closed)
        # Higher weight for weekdays being open
        days = ''
        for i in range(7):
            if i < 5:  # Weekday
                days += '1' if random.random() < 0.8 else '0'
            else:  # Weekend
                days += '1' if random.random() < 0.3 else '0'
        
        # Generate random start time (0000-1200)
        start_hour = str(random.randint(4, 12)).zfill(2)
        start_min = str(random.randint(0, 59)).zfill(2)
        start = f"{start_hour}{start_min}"
        
        # Generate random end time (1200-2359)
        end_hour = str(random.randint(14, 24)).zfill(2)
        end_min = str(random.randint(0, 59)).zfill(2)
        end = f"{end_hour}{end_min}"
        
        hours.append({
            "day": days,
            "start": start,
            "end": end
        })
    
    return {"hours": hours}

def main():
    """Main function to create and populate mock database"""
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters
    db_params = {
        'dbname': os.getenv('DB_NAME', 'optimat'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("\nCreating mock database for testing...")
    print("=====================================")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Execute the mock database creation steps
        create_mock_table(cur)
        copy_provider_data(cur)
        
        print("=====================================")
        print("✓ Mock database created successfully")
        
    except Exception as e:
        print("=====================================")
        print(f"✗ Failed to create mock database: {str(e)}")
        raise
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
