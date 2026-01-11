#!/usr/bin/env python3
"""
Test InfluxDB v3 connection at 10.1.166.48:8181
"""

import sys
sys.path.insert(0, '/opt/Varken')

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

print("=" * 60)
print("Testing InfluxDB v3 at 10.1.166.48:8181")
print("=" * 60)

# Your InfluxDB v3 config
url = "http://10.1.166.48:8181"
token = "apiv3_KyyLFpJl8Z8izei1J1wgDY6vjgqmGoHxBnZH27b9CaTR28-JpEUjvvIhOBOO-2p2JYyDONeMgT7nbFll8Zk6f"
org = "luviaman"
bucket = "varken"

print(f"\nURL: {url}")
print(f"Org: {org}")
print(f"Bucket: {bucket}")
print()

try:
    # Create client
    print("1. Creating client...")
    client = InfluxDBClient(
        url=url,
        token=token,
        org=org,
        timeout=10000,
        verify_ssl=False
    )
    print("   ✓ Client created")
    
    # Test health
    print("\n2. Testing health...")
    health = client.health()
    print(f"   Status: {health.status}")
    print(f"   Message: {health.message}")
    print(f"   Version: {health.version}")
    
    # Test ping
    print("\n3. Testing ping...")
    ping = client.ping()
    print(f"   ✓ Ping successful: {ping}")
    
    # Create write API
    print("\n4. Creating write API...")
    write_api = client.write_api(write_options=SYNCHRONOUS)
    print("   ✓ Write API created")
    
    # Test write
    print("\n5. Testing write...")
    test_line = "test,source=debug value=1i"
    print(f"   Writing: {test_line}")
    
    write_api.write(bucket=bucket, org=org, record=test_line)
    print("   ✓ Write successful!")
    
    # Test query
    print("\n6. Testing query...")
    query_api = client.query_api()
    query = f'from(bucket: "{bucket}") |> range(start: -1m) |> filter(fn: (r) => r._measurement == "test") |> limit(n: 1)'
    result = query_api.query(query, org=org)
    
    if result:
        print("   ✓ Query successful - found data:")
        for table in result:
            for record in table.records:
                print(f"      {record.values}")
    else:
        print("   ✓ Query successful - no data yet (write may be delayed)")
    
    client.close()
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nInfluxDB v3 is working correctly.")
    print("The issue may be with:")
    print("  1. Token/org/bucket mismatch in Varken config")
    print("  2. Network issue during write (intermittent)")
    print("  3. Write API configuration issue")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Troubleshooting:")
    print("=" * 60)
    print("\n1. Check InfluxDB v3 is running:")
    print("   curl http://10.1.166.48:8181/health")
    print("\n2. Check credentials in varken.ini:")
    print("   - token")
    print("   - org")
    print("   - bucket")
    print("\n3. Check InfluxDB v3 logs:")
    print("   docker logs influxdb3  # if using Docker")
    print("   journalctl -u influxdb  # if using systemd")
    print("\n4. Verify bucket exists:")
    print("   influx bucket list --org YOUR_ORG --token YOUR_TOKEN")
