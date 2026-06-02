# Running agentD on Termux (Android)

agentD runs on [Termux](https://termux.dev) as a **lean headless core**: the
agent loop plus HTTP providers (Xiaomi/mimo, Kimi) and the Claude CLI provider.
Browser automation is intentionally disabled — see [Limitations](#limitations).

This is the `port/termux` branch, which diverges from `main` to keep the
dependency set Termux-installable.

## What works / what doesn't

| Capability | Termux | Notes |
|---|---|---|
| `D -n 'task'` (non-interactive) | ✅ | The guaranteed path. |
| Interactive Textual TUI (`D` with no args) | ➖ | Needs `deepagents-cli` (the `deepagents` engine), an opt-in `[tui]` extra that pulls `langgraph-api → grpcio`; grpcio's pip sdist won't build on bionic, so the lean core ships the `D -n` path instead. See [Limitations](#limitations). |
| Xiaomi/mimo provider | ✅ | Pure HTTP (`httpx`). Recommended primary. |
| Kimi provider | ✅ | Pure HTTP. |
| Claude CLI provider (`agentd-cli`) | ✅ | Shells out to the Node `claude` binary (npm-installed). Gives the LLM a Bash tool. |
| Session persistence / memory | ✅ | SQLite checkpointer under `~/.agentd/` (installed `--no-deps`, see [Limitations](#limitations)). Falls back to in-memory if absent. |
| Browser automation (`browser_task`) | ❌ | Playwright's Chromium is a glibc ELF; can't run on bionic libc. Returns a friendly "unavailable" message. |
| Firecrawl / Tavily research | ➖ | Pure HTTP and would work, but kept out of the lean install. Add with `pip install -e '.[research]'`. |

## Install

```bash
pkg install git
git clone https://github.com/nimikest-ui/agentD.git
cd agentD
git checkout port/termux
bash setup-termux.sh
```

`setup-termux.sh` installs the Termux toolchain + prebuilt native packages, creates
a venv, runs `pip install -e .` (lean core, no browser/TUI extras), installs the
SQLite checkpointer `--no-deps`, and optionally installs the Claude CLI via npm.

> **The install compiles a handful of Rust/C packages from source** (pydantic-core,
> jiter, cryptography, orjson, …) because PyPI's prebuilt wheels are glibc and Termux
> needs bionic builds. The heavy gRPC build is **gone** from the lean core — it only
> entered via the opt-in TUI engine (see [Limitations](#limitations)) — so expect
> roughly **10–20 min** on a phone. Two things commonly kill native builds: Android
> suspending Termux in the background, and out-of-memory during parallel compiles.
> The script mitigates both (acquires a `termux-wake-lock` if available, scales build
> parallelism to your RAM — 1 job under 5 GB, 2 jobs at 5–8 GB, 4 above). **Keep the
> screen on and the phone plugged in.** If it stops abruptly with no error, it was
> killed — just re-run; `pip` resumes from its cache. For a reliable wakelock first
> run `pkg install termux-api`.

### Manual install

```bash
pkg install python nodejs-lts rust binutils clang make openssl libxml2 libxslt libjpeg-turbo zlib pkg-config
python -m venv venv && source venv/bin/activate
pip install -e .                      # lean core (no grpc/browser/TUI stack)
# Persistent SQLite checkpointing — install WITHOUT deps to skip the
# Android-incompatible sqlite-vec (the checkpointer never uses it):
pip install --no-deps 'langgraph-checkpoint-sqlite>=3.1.0'
# optional pinned alternative: pip install -r requirements-termux.txt
```

## Configure a provider

Set the API key for whichever provider you want, then select it per-run with `-M`
(the model name auto-selects the provider):

```bash
# Xiaomi/mimo (recommended primary) — pure HTTP, no extra binaries
export XIOMIMIMO_API_KEY=sk-...
D -M mimo-v2.5-pro -n 'summarize the OWASP top 10'

# Kimi — pure HTTP
export MOONSHOT_API_KEY=sk-...
D -M kimi-k2.6 -n 'task'

# Claude CLI provider — needs the Node `claude` binary + a login
npm install -g @anthropic-ai/claude-code
claude            # log in once
D -M haiku -n 'task'   # 'haiku' resolves to the agentd-cli provider
```

To make a provider the default (so `D -n` needs no `-M`), set it in
`~/.deepagents/config.toml`:

```toml
[models]
default = "mimo-v2.5-pro"
```

Or export `AGENTD_PROVIDER` (e.g. `xiomimimo`, `kimi`, `agentd-cli`). Keys can
also be set interactively with `/auth` inside the TUI.

## Limitations

- **No browser automation.** Playwright ships a glibc-linked Chromium that the
  Termux bionic loader can't run, and Playwright provides no bionic build. Calls
  to `browser_task()` / the `browser_run` MCP tool return an "unavailable"
  message. Everything else is unaffected because the core agent graph never
  imports the browser stack (it's lazy/guarded).
- **No interactive TUI in the lean core (`D` with no args).** The TUI *engine* is
  the separate `deepagents-cli` package, which pulls `langgraph-cli[inmem] →
  langgraph-api → grpcio` + `grpcio-tools`. grpcio's pip sdist does not build on
  bionic, and Termux's own prebuilt grpcio is **1.81.0** — outside langgraph-api's
  `grpcio<1.81.0` pin — so it can't substitute either. The lean core therefore omits
  `deepagents-cli`; running bare `D` prints a "TUI engine not found" message. Use the
  guaranteed **`D -n 'task'`** path instead (with the Claude CLI provider it still
  gives the LLM a Bash tool). On a glibc desktop the TUI is available via
  `pip install -e '.[tui]'` (or `.[full]`). agentD's `D -n` path never imports
  deepagents-cli — `auth_store.py`/`mcp_server.py` guard the import — so credential
  *reads* still work from environment variables; only `/auth`-style credential
  *writes* need the extra.
- **SQLite checkpointer installs `--no-deps`.** `langgraph-checkpoint-sqlite`
  hard-requires `sqlite-vec` (a SQLite extension for its *vector store*), which
  ships wheels only — there's no Android/bionic build and no sdist — so a normal
  `pip install` of it can't resolve and makes the whole lean install fail
  (`No matching distribution found for sqlite-vec` / `resolution-too-deep`). The
  `SqliteSaver` checkpointer agentD actually uses never imports `sqlite-vec`, so
  the setup script installs the package with `pip install --no-deps`. The vector
  store is unavailable (agentD uses an in-memory store anyway). If you skip this
  step, `persistence.py` automatically falls back to an in-memory checkpointer —
  the agent runs fine, but sessions won't persist across restarts.
- **On-device LLMs (local Ollama)** are impractical on phone RAM; use the HTTP
  providers (mimo/kimi) or remote Ollama Cloud instead.
