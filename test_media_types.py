#!/usr/bin/env python3
"""
Diagnostic to test different media types (episodes vs movies)
This will help identify if the crash is specific to TV episodes
"""

import sys
import json
sys.path.insert(0, '/opt/Varken')

from varken.iniparser_v2 import EnhancedINIParser
from varken.dbmanager_v2 import MultiDBManager

print("=" * 80)
print("Media Type Handling Diagnostic")
print("=" * 80)

# Load config
print("\n1. Loading configuration...")
CONFIG = EnhancedINIParser('/opt/Varken/data/varken.ini')
print("   ✓ Config loaded")

# Initialize DB manager
print("\n2. Initializing database manager...")
db_configs = CONFIG.get_enabled_databases()
DBManager = MultiDBManager(db_configs)
print(f"   ✓ Connected to {len(DBManager.backends)} database(s)")

# Test writing different media types
print("\n3. Testing different media type writes...")

# Simulate a movie stream
print("\n   Testing MOVIE stream...")
movie_data = [
    {
        'measurement': 'tautulli',
        'tags': {
            'type': 'current_stream',
            'server': '1',
            'media_type': 'movie',
            'session_id': 'test_movie_123'
        },
        'fields': {
            'title': 'Test Movie',
            'username': 'testuser',
            'player_state': 'playing',
            'stream_count': 1,
            'progress_percent': 25
        },
        'time': '2026-01-11T05:50:00+00:00'
    }
]

try:
    results = DBManager.write_points(movie_data)
    success_count = sum(1 for v in results.values() if v)
    print(f"   Movie write: {success_count}/{len(results)} databases succeeded")
    for db, success in results.items():
        status = "✓" if success else "✗"
        print(f"     {status} {db}")
except Exception as e:
    print(f"   ✗ Movie write failed: {e}")
    import traceback
    traceback.print_exc()

# Simulate an episode stream
print("\n   Testing EPISODE stream...")
episode_data = [
    {
        'measurement': 'tautulli',
        'tags': {
            'type': 'current_stream',
            'server': '1',
            'media_type': 'episode',
            'session_id': 'test_episode_456'
        },
        'fields': {
            'title': 'Test Show - S01E01',
            'grandparent_title': 'Test Show',
            'parent_title': 'Season 1',
            'username': 'testuser',
            'player_state': 'playing',
            'stream_count': 1,
            'progress_percent': 50,
            'season': 1,
            'episode': 1
        },
        'time': '2026-01-11T05:50:10+00:00'
    }
]

try:
    results = DBManager.write_points(episode_data)
    success_count = sum(1 for v in results.values() if v)
    print(f"   Episode write: {success_count}/{len(results)} databases succeeded")
    for db, success in results.items():
        status = "✓" if success else "✗"
        print(f"     {status} {db}")
except Exception as e:
    print(f"   ✗ Episode write failed: {e}")
    import traceback
    traceback.print_exc()

# Test with multiple streams (mixed media types)
print("\n   Testing MIXED streams (movie + episode)...")
mixed_data = [
    {
        'measurement': 'tautulli',
        'tags': {
            'type': 'current_stream',
            'server': '1',
            'media_type': 'movie',
            'session_id': 'mixed_movie'
        },
        'fields': {
            'title': 'Movie A',
            'username': 'user1',
            'player_state': 'playing'
        },
        'time': '2026-01-11T05:50:20+00:00'
    },
    {
        'measurement': 'tautulli',
        'tags': {
            'type': 'current_stream',
            'server': '1',
            'media_type': 'episode',
            'session_id': 'mixed_episode'
        },
        'fields': {
            'title': 'Show B - S02E05',
            'grandparent_title': 'Show B',
            'parent_title': 'Season 2',
            'username': 'user2',
            'player_state': 'playing',
            'season': 2,
            'episode': 5
        },
        'time': '2026-01-11T05:50:20+00:00'
    }
]

try:
    results = DBManager.write_points(mixed_data)
    success_count = sum(1 for v in results.values() if v)
    print(f"   Mixed write: {success_count}/{len(results)} databases succeeded")
    for db, success in results.items():
        status = "✓" if success else "✗"
        print(f"     {status} {db}")
except Exception as e:
    print(f"   ✗ Mixed write failed: {e}")
    import traceback
    traceback.print_exc()

# Test with problematic field combinations
print("\n   Testing EPISODE with special characters...")
episode_special = [
    {
        'measurement': 'tautulli',
        'tags': {
            'type': 'current_stream',
            'server': '1',
            'media_type': 'episode',
            'session_id': 'special_chars'
        },
        'fields': {
            'title': 'Show: The "Best" Episode',
            'grandparent_title': 'Show & More',
            'parent_title': 'Season 1, Part A',
            'username': 'user@domain.com',
            'player_state': 'playing',
            'quality_profile': 'HD-1080p/Surround',
            'progress_percent': 75.5,
            'season': 1,
            'episode': 1
        },
        'time': '2026-01-11T05:50:30+00:00'
    }
]

try:
    results = DBManager.write_points(episode_special)
    success_count = sum(1 for v in results.values() if v)
    print(f"   Special chars write: {success_count}/{len(results)} databases succeeded")
    for db, success in results.items():
        status = "✓" if success else "✗"
        print(f"     {status} {db}")
except Exception as e:
    print(f"   ✗ Special chars write failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Summary")
print("=" * 80)
print("\nIf episode writes fail but movie writes succeed,")
print("the issue is likely with episode-specific fields like:")
print("  - grandparent_title")
print("  - parent_title")
print("  - season/episode numbers")
print("  - special characters in show names")
print("\nCheck logs above for which database(s) failed.")
print("=" * 80)
