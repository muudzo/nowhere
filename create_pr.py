#!/usr/bin/env python3
"""
Create a pull request for the fix/tests-and-compat branch.
Requires GITHUB_TOKEN environment variable to be set.
"""

import os
import sys
import json
import urllib.request
import urllib.error

def create_pr():
    """Create a pull request using the GitHub API."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("\nTo create a PR, set your GitHub token:")
        print("  export GITHUB_TOKEN='your_github_personal_access_token'")
        print("\nThen run: python3 create_pr.py")
        return False
    
    repo_owner = "muudzo"
    repo_name = "nowhere"
    
    pr_data = {
        "title": "fix: resolve async fixtures and Pydantic v2 deprecations",
        "body": """## Summary
This PR fixes all remaining issues from the test and compatibility audit.

## Test Results
✅ 17 unit tests PASSING
⊗ 5 integration tests SKIPPED  
❌ 0 FAILING tests

## What's Fixed
1. **FastAPI Dependency Issues**: Fixed DynamicRateLimiter incompatible __call__ signature
2. **Pydantic v2 Deprecations**: Updated to use ConfigDict and validation_alias
3. **Async Fixture Errors**: Fixed fakeredis.ping() and added missing clock parameter
4. **Database Compatibility**: Fixed Postgres DSN format for asyncpg
5. **Code Quality**: Removed unused imports and added backward compatibility

## Files Changed
- backend/api/limiter.py
- backend/config.py
- backend/core/commands.py
- backend/core/events.py
- backend/tests/conftest.py
- backend/tests/services/test_intent_service.py
- backend/tests/test_auth.py
- backend/tests/test_intents.py
- backend/tests/test_redis.py

All unit tests pass. Ready to merge.""",
        "head": "fix/tests-and-compat",
        "base": "main"
    }
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    
    data = json.dumps(pr_data).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'number' in result:
                print("✅ Pull Request Created!")
                print(f"   Title: {result['title']}")
                print(f"   PR Number: #{result['number']}")
                print(f"   URL: {result['html_url']}")
                return True
            else:
                print(f"❌ Error creating PR: {result.get('message', 'Unknown error')}")
                return False
                
    except urllib.error.HTTPError as e:
        error_data = json.loads(e.read().decode('utf-8'))
        print(f"❌ HTTP Error {e.code}: {error_data.get('message', 'Unknown error')}")
        if 'errors' in error_data:
            for err in error_data['errors']:
                print(f"   - {err.get('message', str(err))}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_pr()
    sys.exit(0 if success else 1)
