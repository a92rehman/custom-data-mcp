# Versioning

## Automatic Version Bump Before Push

**ALWAYS bump the version before pushing to GitHub.** This is mandatory — no exceptions.

Before running `git push`, run one of:
- `python -m custom_data_mcp bump` — patch bump (0.3.1 → 0.3.2) for fixes, docs, small changes
- `python -m custom_data_mcp bump --minor` — minor bump (0.3.2 → 0.4.0) for new features, bigger releases

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
3. `python -m custom_data_mcp bump` (or `bump --minor`)
4. `git add -A && git commit -m "chore: bump version to vX.Y.Z"`
5. `git tag vX.Y.Z`
6. `git push origin master --tags && git push origin master:main --tags`

**The git tag is critical** — users' session-start hooks check `git ls-remote --tags` to find the latest version. Without a tag, users won't see the update.

Never push without bumping. Users check `/mcp` and `version` command to know what they're running.

## How Rules Reach Users

The session-start hook automatically downloads the latest rules on every session:
1. Writes `~/.claude/custom-data-rules-path` with the absolute path to the rules directory (so the agent can find them)
2. Checks `git ls-remote --tags` against `~/.claude/custom-data-rules-version`
3. If newer tag exists: shallow-clones tag, extracts `rules/` into plugin cache directory
4. Updates `~/.claude/custom-data-rules-path` again (rules may have moved to a new version directory)
5. Checks at most once every 6 hours (skips if recently checked)
6. Fallback: uses existing plugin cache rules if network unavailable

Rules auto-update. No manual reinstall needed.

## What `bump` Does

Running `python -m custom_data_mcp bump` also:
- Syncs rules to `src/custom_data_mcp/rules/` and `rules/`
- Updates `.claude-plugin/plugin.json` and `marketplace.json` version fields
- Updates `.current-version`

## When Changing Rules: Update Checklist

When adding, editing, or removing governance rules, also update:
1. **`rules/index.md`** — add/update the routing entry for the new rule file
2. **`projects.yaml`** — add/update the project entry if a new region or dataset is involved
3. **`README.md`** — update the Regions & Datasets table if a region changed
4. **`CLAUDE.md`** — update if architecture or project structure changed
5. **`docs/INSTALL.md`** — update if setup flow changed
6. **Dashboard** — `projects.yaml` drives the Governance page; new datasets appear automatically
7. **Agent descriptions** — update `agents/data-analyst.md` description if new region or domain added

Rules are NOT placed in `~/.claude/rules/` — that bypasses the agent's governance flow.
Rules live only in the plugin's `rules/` directory, read by the data-analyst subagent.
