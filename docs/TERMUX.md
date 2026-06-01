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
| Interactive Textual TUI (`D`) | ✅ | `deepagents` is a pip/Textual TUI, runs in the Termux terminal. |
| Xiaomi/mimo provider | ✅ | Pure HTTP (`httpx`). Recommended primary. |
| Kimi provider | ✅ | Pure HTTP. |
| Claude CLI provider (`agentd-cli`) | ✅ | Shells out to the Node `claude` binary (npm-installed). Gives the LLM a Bash tool. |
| Session persistence / memory | ✅ | SQLite checkpointer under `~/.agentd/`. |
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

`setup-termux.sh` installs the Termux toolchain + prebuilt native wheels, creates
a venv, runs `pip install -e .` (lean core, no browser extra), and optionally
installs the Claude CLI via npm.

> **The install compiles several Rust/C packages from source** (pydantic-core,
> jiter, tiktoken, …) because PyPI's prebuilt wheels are glibc and Termux needs
> bionic builds. This takes **20–40 min** on a phone. Two things commonly kill it:
> Android suspending Termux in the background, and out-of-memory during parallel
> compiles. The script mitigates both (acquires a `termux-wake-lock` if available,
> scales build parallelism to your RAM — 1 job under 5 GB, 2 jobs at 5–8 GB, 4
above). **Keep the screen on and
> the phone plugged in.** If it stops abruptly with no error, it was killed — just
> re-run; `pip` resumes from its cache. For a reliable wakelock first run
> `pkg install termux-api`.

### Manual install

```bash
pkg install python nodejs-lts rust binutils clang make openssl libxml2 libxslt libjpeg-turbo zlib
python -m venv venv && source venv/bin/activate
pip install -e .                      # lean core
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
- **`grpcio`** is not in the lean install (no provider here needs it). If a future
  dependency pulls it and the build fails, set
  `GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1 GRPC_PYTHON_BUILD_SYSTEM_ZLIB=1` before
  `pip install` (the setup script already exports these).
- **On-device LLMs (local Ollama)** are impractical on phone RAM; use the HTTP
  providers (mimo/kimi) or remote Ollama Cloud instead.
