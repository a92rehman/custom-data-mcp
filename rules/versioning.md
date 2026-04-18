# Versioning

## Automatic Version Bump Before Push

**ALWAYS bump the version before pushing to GitHub.** This is mandatory — no exceptions.

Before running `git push`, run one of:
- `python -m taleemabad_data_mcp bump` — patch bump (0.3.1 → 0.3.2) for fixes, docs, small changes
- `python -m taleemabad_data_mcp bump --minor` — minor bump (0.3.2 → 0.4.0) for new features, bigger releases

This updates both `__init__.py` and `pyproject.toml` automatically.

## Which Bump to Use

| Change Type | Bump | Example |
|-------------|------|---------|
| Bug fix, typo, doc update | `bump` (patch) | 0.3.1 → 0.3.2 |
| Rule file additions or edits | `bump` (patch) | 0.3.2 → 0.3.3 |
| New MCP tool, new CLI command | `bump --minor` | 0.3.3 → 0.4.0 |
| New dashboard page, new region | `bump --minor` | 0.4.0 → 0.5.0 |
| Breaking change to existing tools | `bump --minor` | 0.5.0 → 0.6.0 |

## Push Workflow

1. `git add -A`
2. `git commit -m "description"`
3. `python -m taleemabad_data_mcp bump` (or `bump --minor`)
4. `git add -A && git commit -m "chore: bump version to vX.Y.Z"`
5. `git tag vX.Y.Z`
6. `git push origin master --tags && git push origin master:main --tags`

**The git tag is critical** — users' session-start hooks check `git ls-remote --tags` to find the latest version. Without a tag, users won't see the update.

Never push without bumping. Users check `/mcp` and `version` command to know what they're running.

## How Rules Reach Users

The session-start hook automatically downloads the latest rules on every session:
1. Checks `git ls-remote --tags` against `~/.claude/taleemabad-rules-version`
2. If newer tag exists: shallow-clones tag, extracts `rules/` into plugin cache directory
3. Checks at most once every 6 hours (skips if recently checked)
4. Fallback: uses existing plugin cache rules if network unavailable

Rules auto-update. No manual reinstall needed.

## What `bump` Does

Running `python -m taleemabad_data_mcp bump` also:
- Syncs rules to `src/taleemabad_data_mcp/rules/` and `rules/`
- Updates `.claude-plugin/plugin.json` and `marketplace.json` version fields
- Updates `.current-version`
