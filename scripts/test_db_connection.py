#!/usr/bin/env python
"""
Test database connection and verify TimescaleDB is properly configured.
"""
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor


def test_connection(max_retries=5, retry_delay=2):
    """Test database connection with retries."""
    connection_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'aetherlens',
        'user': 'postgres',
        'password': 'aetherlens_pass'
    }

    print("Testing PostgreSQL/TimescaleDB connection...")
    print(f"Host: {connection_params['host']}")
    print(f"Port: {connection_params['port']}")
    print(f"Database: {connection_params['database']}")
    print()

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}...", end=" ")
            conn = psycopg2.connect(**connection_params)
            conn.autocommit = True
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            print("✅ Connected!")

            # Test 1: Check PostgreSQL version
            cursor.execute("SELECT version();")
            pg_version = cursor.fetchone()['version']
            print(f"\n📊 PostgreSQL Version:")
            print(f"   {pg_version}")

            # Test 2: Check TimescaleDB extension
            cursor.execute("""
                SELECT extname, extversion
                FROM pg_extension
                WHERE extname = 'timescaledb';
            """)
            result = cursor.fetchone()

            if result:
                print(f"\n✅ TimescaleDB Extension:")
                print(f"   Name: {result['extname']}")
                print(f"   Version: {result['extversion']}")
            else:
                print("\n❌ TimescaleDB extension not found!")
                return False

            # Test 3: Check database configuration
            cursor.execute("""
                SELECT name, setting, unit
                FROM pg_settings
                WHERE name IN ('shared_preload_libraries', 'max_connections', 'shared_buffers');
            """)
            print(f"\n⚙️  Database Configuration:")
            for row in cursor.fetchall():
                unit = f" {row['unit']}" if row['unit'] else ""
                print(f"   {row['name']}: {row['setting']}{unit}")

            # Test 4: Check TimescaleDB functions
            cursor.execute("""
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_schema = 'public'
                  AND routine_name LIKE 'create_hypertable%'
                LIMIT 1;
            """)
            result = cursor.fetchone()
            if result:
                print(f"\n✅ TimescaleDB Functions: Available")
            else:
                print(f"\n⚠️  TimescaleDB Functions: Not found")

            # Test 5: Simple query test
            cursor.execute("SELECT NOW() as current_time;")
            current_time = cursor.fetchone()['current_time']
            print(f"\n🕐 Current Time: {current_time}")

            cursor.close()
            conn.close()

            print("\n" + "="*60)
            print("✅ All tests passed! Database is ready.")
            print("="*60)
            return True

        except psycopg2.OperationalError as e:
            print(f"❌ Failed")
            if attempt < max_retries:
                print(f"   Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"\n❌ Connection failed after {max_retries} attempts")
                print(f"Error: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
