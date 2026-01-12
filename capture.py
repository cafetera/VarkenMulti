#!/usr/bin/env python3
"""
Capture raw Tautulli activity data to see what's being sent
Run this while an episode is playing
"""

import sys
import json
import requests
sys.path.insert(0, '/opt/Varken')

from varken.iniparser_v2 import EnhancedINIParser

print("=" * 80)
print("Tautulli Raw Data Capture")
print("=" * 80)

# Load config
print("\n1. Loading configuration...")
CONFIG = EnhancedINIParser('/opt/Varken/data/varken.ini')
print("   ✓ Config loaded")

# Get Tautulli server
if not hasattr(CONFIG, 'tautulli_servers') or not CONFIG.tautulli_servers:
    print("   ✗ No Tautulli servers configured!")
    sys.exit(1)

server = CONFIG.tautulli_servers[0]
print(f"\n2. Tautulli server: {server.url}")

# Fetch activity
print("\n3. Fetching current activity...")
try:
    url = f"{server.url}/api/v2"
    params = {
        'apikey': server.api_key,
        'cmd': 'get_activity'
    }
    
    response = requests.get(url, params=params, verify=server.verify_ssl, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if data.get('response', {}).get('result') != 'success':
        print(f"   ✗ Tautulli API error: {data}")
        sys.exit(1)
    
    activity = data.get('response', {}).get('data', {})
    sessions = activity.get('sessions', [])
    
    print(f"   ✓ Found {len(sessions)} active session(s)")
    
    if not sessions:
        print("\n⚠️  No active streams!")
        print("   Start playing something in Plex and run this again.")
        sys.exit(0)
    
    # Show each session
    for i, session in enumerate(sessions, 1):
        print(f"\n{'=' * 80}")
        print(f"Session {i}:")
        print('=' * 80)
        
        # Basic info
        print(f"\nMedia Type: {session.get('media_type', 'unknown')}")
        print(f"Title: {session.get('title', 'unknown')}")
        print(f"User: {session.get('username', 'unknown')}")
        print(f"Player State: {session.get('player_state', 'unknown')}")
        
        # Episode-specific fields
        if session.get('media_type') == 'episode':
            print(f"\n📺 Episode Details:")
            print(f"  Show: {session.get('grandparent_title', 'N/A')}")
            print(f"  Season: {session.get('parent_media_index', 'N/A')}")
            print(f"  Episode: {session.get('media_index', 'N/A')}")
            print(f"  Season Title: {session.get('parent_title', 'N/A')}")
        
        # Movie-specific fields
        if session.get('media_type') == 'movie':
            print(f"\n🎬 Movie Details:")
            print(f"  Year: {session.get('year', 'N/A')}")
            print(f"  Rating: {session.get('rating', 'N/A')}")
        
        # Check for problematic fields
        print(f"\n🔍 Checking for potential issues:")
        
        problematic_fields = []
        
        # Check for None values
        for key, value in session.items():
            if value is None:
                problematic_fields.append(f"  ⚠️  {key} = None")
        
        # Check for special characters
        string_fields = ['title', 'grandparent_title', 'parent_title', 'username']
        for field in string_fields:
            value = session.get(field)
            if value and isinstance(value, str):
                special_chars = [c for c in value if c in '",=: \\']
                if special_chars:
                    problematic_fields.append(f"  ⚠️  {field} has special chars: {set(special_chars)}")
        
        if problematic_fields:
            print("\n".join(problematic_fields))
        else:
            print("  ✓ No obvious problems detected")
        
        # Show ALL fields (for debugging)
        print(f"\n📋 All fields ({len(session)} total):")
        for key in sorted(session.keys()):
            value = session[key]
            value_str = str(value)[:100]  # Truncate long values
            print(f"  {key}: {value_str}")
    
    # Save to file for detailed analysis
    output_file = '/tmp/tautulli_raw_data.json'
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"✓ Full raw data saved to: {output_file}")
    print("=" * 80)
    
except requests.exceptions.RequestException as e:
    print(f"   ✗ Request failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n💡 If you see special characters or None values above,")
print("   those might be causing the database write to fail/hang.")
