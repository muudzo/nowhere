# Pull Request Instructions

The `fix/tests-and-compat` branch has been successfully updated with all fixes. To create the pull request, follow these steps:

## Option 1: Using GitHub Web Interface (Recommended)

1. Go to https://github.com/muudzo/nowhere
2. Click on "Pull Requests" tab
3. Click "New Pull Request" button
4. Set:
   - **Base branch:** `main`
   - **Compare branch:** `fix/tests-and-compat`
5. Use the following details:

### PR Title
```
fix: resolve async fixtures and Pydantic v2 deprecations
```

### PR Description
```markdown
## Summary
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

All unit tests pass. Ready to merge.
```

6. Click "Create Pull Request"

## Option 2: Using GitHub CLI

If you have GitHub CLI installed and authenticated:

```bash
gh pr create \
  --title "fix: resolve async fixtures and Pydantic v2 deprecations" \
  --body "Fixes all remaining issues from the test and compatibility audit.

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

All unit tests pass. Ready to merge." \
  --base main \
  --head fix/tests-and-compat
```

## Option 3: Using Python (requires GITHUB_TOKEN)

```bash
export GITHUB_TOKEN="your_github_token_here"
python3 create_pr.py
```

## Verification

After the PR is created, you should see:
- ✅ All checks passing (17 unit tests)
- ✅ No merge conflicts
- ✅ Branch is up to date with main
- ✅ Ready to merge notification

## Merge Instructions

Once the PR is created and reviewed:

1. Click the "Merge pull request" button on GitHub
2. Select "Squash and merge" or "Create a merge commit" (your preference)
3. Delete the branch after merge

---

**Summary of Changes:**
- Fixed DynamicRateLimiter FastAPI dependency injection
- Updated all Pydantic models to v2 syntax
- Fixed async fixture errors in tests
- Ensured full test suite compatibility
- All unit tests passing ✅
