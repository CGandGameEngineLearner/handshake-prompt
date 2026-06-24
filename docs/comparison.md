# Comparison with Existing Approaches

How does the Handshake Prompt Protocol compare to other ways of letting an
AI Agent access a service on behalf of a user?

## At a glance

|                                   | API Key      | OAuth 2.0          | MCP Server     | Handshake Prompt    |
|-----------------------------------|--------------|--------------------|----------------|---------------------|
| **User must configure something** | Yes          | Partial (consent)  | Yes            | **No** — just paste |
| **Setup steps for user**          | 3–5          | 2–3                | 5–10           | **1**               |
| **Scoped to a single task**       | No           | No                 | No             | **Yes**             |
| **Auto-expires by default**       | No           | No (refresh)       | No             | **Yes (30 min)**    |
| **Revocable per session**         | No           | Per-app            | No             | **Yes (TTL)**       |
| **Works with any Agent**          | If Agent supports keys | Yes (browser) | Only MCP-aware Agents | **Yes**       |
| **Real-time UX**                  | No           | No                 | No             | **Yes (WS push)**   |
| **Protects user-written data**    | No           | No                 | No             | **Yes (by=user lock)** |
| **Backend integration LOC**       | medium       | high               | high           | **~3 lines**        |
| **Long-term identity binding**    | Yes          | Yes                | Yes            | **No**              |

---

## API Key

**The pattern.** User generates a long-lived API key in your service's
dashboard, then pastes it into their Agent's config or environment variable.

**Pros**
- Simple to implement on the server.
- Wide Agent compatibility (most LLM tools support `OPENAI_API_KEY` style env vars).

**Cons**
- **User-hostile setup**: open a dashboard, find the right page, generate
  a key, copy it, find Agent config, paste, save.
- **Long-lived**: a leaked key compromises everything until manually revoked.
- **Global scope**: the Agent can do _anything_ the user can do.
- **Multi-tenant nightmare**: every user manages their own keys for every
  service.

**Handshake Prompt fix.** No key to generate. No place to paste. The
"credential" is one-time and lives inside the prompt itself.

---

## OAuth 2.0

**The pattern.** User clicks "Sign in with X", lands on a consent screen,
clicks "Authorize", redirected back with an access token (often paired with
a refresh token for long-lived access).

**Pros**
- Industry standard, audited.
- Refresh tokens enable long-lived access without user re-consent.
- Server-side revocation is well-defined.

**Cons**
- **Heavy implementation**: OAuth server, scopes, redirect URIs, refresh
  flows, JWT verification, well over 1000 LOC for a robust setup.
- **Per-app**, not per-task: once an Agent has the token, it can do
  anything the scope allows until the user manually revokes.
- **Browser-centric**: doesn't map cleanly to an Agent running locally on
  the user's machine. (Authorization Code with PKCE works, but the user
  still has to deal with redirect URIs.)
- **Refresh-token leakage** is a known problem.

**Handshake Prompt fix.** No flow. The token is generated _after_ the
user is already authenticated (in their browser session), and its lifetime
is bounded by the task at hand.

---

## MCP (Model Context Protocol)

**The pattern.** Service publishes an MCP server. User installs the server
in their Agent's MCP config, supplies any credentials the MCP requires,
restarts the Agent. The Agent now sees the MCP's tools.

**Pros**
- Strong typing and structured tool surface.
- Good for **persistent**, **multi-tool** integrations
  (e.g. a personal note-taking system).

**Cons**
- **High setup friction**: install server binary, edit JSON config, manage
  process lifecycle.
- **Per-Agent**: must be re-installed for each Agent (Claude Desktop,
  Cursor, Continue, etc.).
- **Credential management** is still the user's problem (MCPs typically
  forward API keys).
- **Heavy for one-off tasks**: spinning up an MCP server just to fill one
  form is overkill.

**Handshake Prompt fix.** No installation. No daemon. Works with _any_
Agent that can read text and call HTTP. The user grants access just for
this one task, this one time.

---

## Browser extensions / RPA tools

**The pattern.** A browser extension or RPA tool watches the page and
fills it on behalf of the user (e.g. password managers, form fillers).

**Cons**
- Requires installing extension/tool, granting page-level permissions.
- Hard for the AI to negotiate ambiguity ("which field is the email?").
- The user can't easily switch Agents (the extension is the Agent).

**Handshake Prompt fix.** The service _itself_ exposes a structured action
surface; any Agent can drive it via a simple HTTP API.

---

## QR-code login (analogue)

The most direct analogue. Just like a QR code transfers a one-time
authentication grant from a phone to a web session, a handshake prompt
transfers a one-time _action_ grant from a logged-in web session to an
external Agent.

Both share the same superpower: **the user does one trivial physical action,
and a complex authorization step happens behind the scenes.**

---

## When NOT to use Handshake Prompt

Handshake Prompt is great for **bounded, short-lived tasks**. Use something
else when you need:

- **Long-running automations** without user supervision → API key or service account
- **Multi-tool persistent assistants** that touch many services → MCP
- **Identity federation** between two services → OAuth
- **Background data sync** → API key + webhooks

Use Handshake Prompt when the user is **in the browser, has decided what
they want done, and just wants to hand it to their Agent right now.**
