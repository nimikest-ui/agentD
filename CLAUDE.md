<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **agentD** (2079 symbols, 3026 relationships, 45 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Claude Is In Charge of GitNexus

**I (Claude) own all GitNexus workflows.** I proactively run impact analysis, detect changes, and trace code — without asking for permission. The rules below are non-negotiable for this codebase.

## I Always Do

- **Run impact analysis before editing any symbol.** Before modifying any function, class, or method, I execute `mcp__gitnexus__impact({target: "symbolName", direction: "upstream"})` and report the blast radius to you (direct callers, affected processes, risk level).
- **Run `mcp__gitnexus__detect_changes()` before committing.** I verify that my changes only affect expected symbols and execution flows.
- **Warn you immediately** if impact analysis returns HIGH or CRITICAL risk — I do not proceed with edits without your explicit approval.
- **Use `mcp__gitnexus__query()` for exploration.** Instead of grepping unfamiliar code, I search for execution flows ranked by relevance.
- **Use `mcp__gitnexus__context()` for symbol context.** When I need callers, callees, or which execution flows a symbol participates in, I fetch the full 360-degree view.

## I Never Do

- Never edit a function, class, or method without first running `mcp__gitnexus__impact` on it.
- Never ignore HIGH or CRITICAL risk warnings.
- Never use find-and-replace for renames — I always use `mcp__gitnexus__rename` which understands the call graph.
- Never commit changes without running `mcp__gitnexus__detect_changes()` first.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/agentD/context` | Codebase overview, check index freshness |
| `gitnexus://repo/agentD/clusters` | All functional areas |
| `gitnexus://repo/agentD/processes` | All execution flows |
| `gitnexus://repo/agentD/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
