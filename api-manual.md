# RAG Platform — API Manual

A detailed reference for the RAG platform's HTTP API, with Python (`httpx`) examples
for every endpoint and an in-depth, scenario-driven section on multi-turn
conversation.

> The platform is an offline document-intelligence app: upload PDFs/images →
> OCR → chunk → embed → index → ask questions grounded in the indexed
> documents via a chat UI. This API is the backend behind that UI (and is also
> reachable by external programs — see [Search (public)](#7-search-public)).

---

## Table of contents

1. [Foundations](#1-foundations)
   - [Base URL & transport](#base-url--transport)
   - [Authentication](#authentication)
   - [Conventions](#conventions)
   - [Server-Sent Events primer (the `/chat` stream)](#server-sent-events-primer-the-chat-stream)
   - [Shared data types](#shared-data-types)
   - [Enums reference](#enums-reference)
2. [System](#2-system)
   - [`GET /system/health`](#get-systemhealth)
3. [Documents](#3-documents)
   - [`GET /documents`](#get-documents)
   - [`POST /documents`](#post-documents)
   - [`GET /documents/{doc_id}`](#get-documentsdoc_id)
   - [`GET /documents/{doc_id}/file`](#get-documentsdoc_idfile)
   - [`DELETE /documents/{doc_id}`](#delete-documentsdoc_id)
4. [Jobs](#4-jobs)
   - [`GET /jobs`](#get-jobs)
   - [`POST /jobs/{job_id}/cancel`](#post-jobsjob_idcancel)
   - [`POST /jobs/{job_id}/retry`](#post-jobsjob_idretry)
   - [`PATCH /jobs/{job_id}/priority`](#patch-jobsjob_idpriority)
5. [Chat & Conversations](#5-chat--conversations)
   - [`POST /chat`](#post-chat)
   - [`GET /conversations`](#get-conversations)
   - [`GET /conversations/{conversation_id}/messages`](#get-conversationsconversation_idmessages)
   - [`DELETE /conversations/{conversation_id}/messages/{message_id}`](#delete-conversationsconversation_idmessagesmessage_id)
   - [`PATCH /conversations/{conversation_id}`](#patch-conversationsconversation_id)
   - [`DELETE /conversations/{conversation_id}`](#delete-conversationsconversation_id)
6. [Settings](#6-settings)
   - [`GET /settings/chat`](#get-settingschat)
   - [`PUT /settings/chat`](#put-settingschat)
   - [`GET /settings/models`](#get-settingsmodels)
7. [OpenAI-compatible API (`/v1`)](#7-openai-compatible-api-v1)
   - [`GET /v1/models`](#get-v1models)
   - [`POST /v1/chat/completions`](#post-v1chatcompletions)
8. [Search (public)](#8-search-public)
   - [`POST /search`](#post-search)
9. [Activity](#9-activity)
   - [`GET /activity`](#get-activity)
10. [Multi-turn conversation deep-dive](#10-multi-turn-conversation-deep-dive)
    - [Scenario 1 — Start a conversation](#scenario-1--start-a-conversation)
    - [Scenario 2 — Continue it (an N-turn loop)](#scenario-2--continue-it-an-n-turn-loop)
    - [Scenario 3 — Scope & named-document targeting](#scenario-3--scope--named-document-targeting)
    - [Scenario 4 — Edit-resend a turn](#scenario-4--edit-resend-a-turn)
    - [Scenario 5 — Long conversations & memory](#scenario-5--long-conversations--memory)
    - [Scenario 6 — Failure & cancellation states](#scenario-6--failure--cancellation-states)
11. [Appendix](#11-appendix)
    - [Error catalog](#error-catalog)
    - [Default configuration](#default-configuration)

---

## 1. Foundations

### Base URL & transport

| Environment | Base URL | Notes |
|---|---|---|
| Local dev (backend) | `http://localhost:8000` | Run `.venv/bin/uvicorn backend.main:app --port 8000` from the **repo root**. |
| Local dev (frontend) | `http://localhost:5173` | Vite dev server; talks to the backend via `VITE_API_BASE_URL`. |
| Production (Docker) | `http://<your-host>:<APP_PORT>/` | The built SPA and the API share **one origin/port** — no CORS in prod. Plain HTTP (no TLS termination in the default deployment). |

All paths below are relative to the base URL (e.g. `GET /documents`). The
**example URLs use the local-dev base `http://localhost:8000`**; for the live
deployment, substitute your server's `APP_PORT` (see below).

> **Current deployment ports** (from `Setup/.env`):
> - Web UI + API → `http://<your-host>:1152`  (`APP_PORT=1152`; host `1152` → container `8000`)
> - Qdrant REST → `<your-host>:1153`  (`QDRANT_HTTP_PORT=1153`, for **direct** vector queries by other apps — Qdrant's own REST API, e.g. `/collections/rag_chunks`; not the platform's [`POST /search`](#post-search), which goes through the backend on `APP_PORT`)
> - Qdrant gRPC → `<your-host>:1154`  (`QDRANT_GRPC_PORT=1154`)
>
> So against the live system, e.g. `GET /documents` is
> `http://<your-host>:1152/documents`, and `GET /system/health` is
> `http://<your-host>:1152/system/health`. (The in-container port is always
> `8000` — set by the `Dockerfile`; only the *host* port comes from `APP_PORT`.)

CORS is enabled only for `http://localhost:5173` / `http://127.0.0.1:5173` (dev).
In production the SPA is served same-origin, so cross-origin rules do not apply.

### Authentication

**There is no authentication on the internal API.** Every route declares
`user: User = Depends(current_user)`, but `current_user()` always returns the
same demo user (`DEMO_USER_ID`, default `usr_demo`). No `Authorization` header
is required or read for `/documents`, `/jobs`, `/chat`, `/conversations`, or
`/settings` endpoints.

All data access is scoped by that user id purely for IDOR-safety consistency —
when real auth lands, the same queries will key off a real identity without the
routes changing shape.

**External OpenAI-compatible API (`/v1/*`) and retrieval (`/search`) require a
platform API key.** Generate the key in the web UI at **Settings → External
API** and pass it via `Authorization: Bearer <key>` (or `X-API-Key` for
`/search`). See [§7](#7-openai-compatible-api-v1) for details. **Treat the API
as reachable only on a trusted, firewalled network.**

### Conventions

- **Request bodies** are JSON (`Content-Type: application/json`), except
  [`POST /documents`](#post-documents) which is `multipart/form-data`.
- **Responses** are JSON (UTF-8). The two streaming exceptions are
  [`POST /chat`](#post-chat) (`text/event-stream`) and
  [`GET /documents/{id}/file`](#get-documentsdoc_idfile) (a binary file).
- **Validation errors** from Pydantic come back as FastAPI's default `422`
  with an `{"detail": [...]}` body.
- **Timestamps** are opaque strings (UI-formatted); do not parse them as ISO.
  Ordering endpoints use them internally (`ORDER BY ... ASC/DESC`) — rely on
  the returned order, not on parsing the value.
- **Soft delete.** [`DELETE /documents/{id}`](#delete-documentsdoc_id) sets
  `status="DELETED"` and removes the on-disk file, but the row stays so
  [`GET /activity`](#get-activity) can still resolve historical names.
  [`GET /documents`](#get-documents) **still returns deleted rows** — clients
  must filter `status !== "DELETED"` themselves.

### Server-Sent Events primer (the `/chat` stream)

[`POST /chat`](#post-chat) does not return a JSON body. It returns an SSE
stream (`text/event-stream`) of named events:

```
event: delta
data: {"text": "The "}

event: delta
data: {"text": "policy "}

…

event: done
data: {"citations": [...], "state": "supported", "conversationId": "conv_…", "userMessageId": "msg_…"}

```

Rules:

- **Many** `delta` events, each carrying a `{"text": "…"}` token fragment.
  Concatenate `data.text` in order to reconstruct the answer.
- **Exactly one** terminal `done` event, carrying the metadata below. After it,
  the stream closes.

  | Field | Meaning |
  |---|---|
  | `citations` | The citations **actually referenced** in the answer (see below), not every retrieved passage. |
  | `state` | One of `supported`, `no-result`, `error`, `cancelled` ([Enums](#enums-reference)). |
  | `conversationId` | The conversation this turn belongs to. Pass it back to continue. |
  | `userMessageId` | The id of the user message row persisted for this turn. |

- The answer text is **not** repeated in `done` — it was already delivered as
  `delta` fragments.

**Citation filtering.** Retrieval gathers up to `RAG_TOP_K` candidate passages (default 12) and
numbers them `[1]`…`[n]` in the prompt. The model is told to cite as `[n]`.
After generation the server scans the answer for `[n]` (full-width `【n】`,
and footnote-style `[^n]`) markers and keeps only those citations in
`done.citations`. A `number` field on
each citation ties it back to the `[n]` in the text.

**Consuming SSE with `httpx`** — the canonical pattern used throughout this
manual:

```python
import json
import httpx

def chat(base: str, payload: dict) -> dict:
    """POST /chat, print tokens live, return the `done` payload."""
    answer_parts, done = [], None
    with httpx.stream("POST", f"{base}/chat", json=payload, timeout=None) as r:
        event = None
        for line in r.iter_lines():
            if not line:
                continue
            field, _, value = line.partition(": ")
            if field == "event":
                event = value
            elif field == "data":
                data = json.loads(value)
                if event == "delta":
                    answer_parts.append(data["text"])
                    print(data["text"], end="", flush=True)
                elif event == "done":
                    done = data
    print()  # newline after the streamed answer
    done["_answer"] = "".join(answer_parts)
    return done
```

`timeout=None` matters: a turn can take many seconds (OCR-grounded answers
stream token-by-token from a local LLM), and `httpx`'s default read timeout
would abort the stream.

### Shared data types

These shapes appear across multiple endpoints.

```jsonc
// DocumentOut  — GET /documents, GET /documents/{id}
{
  "id": "doc_abc123",
  "name": "policy-handbook.pdf",
  "type": "PDF",                 // PDF | PNG | JPG | JPEG | GIF | TIFF | BMP | WEBP | FILE
  "size": "2.4 MB",              // human-readable, NOT raw bytes
  "pages": 12,
  "uploaded": "2026-08-10 09:31",   // actual upload time, rendered in DISPLAY_TZ (default Asia/Bangkok); stored internally as UTC
  "status": "RAG READY",         // see Enums
  "stage": "Finalization",       // current/last pipeline stage; may be null
  "rag": "Ready"                 // "Ready" | "Failed" | null
}
```

```jsonc
// JobOut  — GET /jobs
{
  "id": "job_xyz",
  "documentId": "doc_abc123",
  "name": "policy-handbook.pdf",
  "priority": "Normal",          // Normal | Urgent
  "status": "COMPLETED",         // see Enums
  "stage": "Finalization",
  "progress": 100,               // 0 | 25 | 50 | 75 | 100 (stage checkpoints)
  "stageProgress": null,         // reserved; currently unused by the UI
  "page": null,                  // current OCR page during "OCR Processing"
  "pages": 12,                   // total pages (OCR stage)
  "submitted": "2026-08-10 09:30:11",
  "started": "2026-08-10 09:30:12",
  "worker": "worker-1",
  "warnings": 0
}
```

```jsonc
// KnowledgeScope  — used in ChatRequest and ConversationOut
{
  "mode": "all",                 // all | selected
  "documentIds": []              // used only when mode == "selected"; max 100
}
```

```jsonc
// ChatRequest  — POST /chat, POST /search
{
  "question": "What is the remote-work policy?",   // max 4000 chars
  "scope": { "mode": "all", "documentIds": [] },
  "conversationId": null          // omit or null to start a new conversation
}
```

```jsonc
// ChatCitation  — in done.citations and ConversationMessageOut.citations
{
  "id": "cite-1",
  "number": 1,                    // the [n] this citation corresponds to (may be null on old rows)
  "documentId": "doc_abc123",
  "documentName": "policy-handbook.pdf",
  "page": 4,
  "excerpt": "Employees may work remotely up to 3 days/week…"   // first 240 chars
}
```

```jsonc
// ConversationOut  — GET /conversations, PATCH /conversations/{id}
{
  "id": "conv_01J…",
  "title": "What is the remote-work policy?",   // first 60 chars of the first question
  "scope": { "mode": "all", "documentIds": [] },
  "createdAt": "2026-08-10 09:35:00",
  "updatedAt": "2026-08-10 09:36:22"
}
```

```jsonc
// ConversationMessageOut  — GET /conversations/{id}/messages
{
  "id": "msg_01J…",
  "role": "assistant",            // user | assistant | system
  "content": "Employees may work remotely…",
  "citations": [ /* ChatCitation[] */ ],
  "state": "supported",           // supported | no-result | error | cancelled | null (user rows)
  "createdAt": "2026-08-10 09:35:05"
}
```

```jsonc
// ChatSettings  — GET/PUT /settings/chat
{
  "chatModel": "gpt-oss:120b",          // null = use global default
  "systemPrompt": null,                 // null = use global default
  "temperature": 0.2                    // null = use global default; range 0..2
}
```

### Enums reference

| Enum context | Allowed values |
|---|---|
| **Document `status`** | `UPLOADED` → `PROCESSING` → `RAG READY` \| `FAILED` \| `CANCELLED` \| `DELETED` |
| **Document `stage`** | `OCR Processing`, `Chunking`, `Embedding Generation`, `Vector Indexing`, `Finalization`, `Cancelled`, `Failed` |
| **Document `rag`** | `Ready` \| `Failed` \| `null` |
| **Job `status`** | `WAITING` → `RUNNING` → `COMPLETED` \| `FAILED` \| `CANCELLED` |
| **Job `stage`** | `Waiting`, `OCR Processing`, `Chunking`, `Embedding Generation`, `Vector Indexing`, `Finalization`, `Cancelled`, `Failed` |
| **Job `progress`** | `0` (waiting) · `25` (OCR) · `50` (Chunking) · `75` (Embedding) · `100` (Indexing/Finalization) |
| **Job `priority`** | `Normal` \| `Urgent` |
| **Message `state`** | `supported` \| `no-result` \| `error` \| `cancelled` |
| **Scope `mode`** | `all` \| `selected` |

---

## 2. System

### `GET /system/health`

Liveness/health of the platform's dependencies. Probes Qdrant and Ollama over
HTTP with short timeouts and returns a fixed table the UI renders directly.

**Response `200`** — `array of [name, state, metric]` rows:

```json
[
  ["Backend API",          "Healthy", "0"],
  ["Database",             "Healthy", "7"],
  ["File Storage",         "Healthy", "—"],
  ["Job Queue",            "Healthy", "0"],
  ["OCR Worker",           "Healthy", "0"],
  ["Embedding Worker",     "Healthy", "0"],
  ["Vector Database",      "Healthy", "0"],
  ["Local Model Runtime",  "Healthy", "0"]
]
```

`state` is one of `Healthy` \| `Degraded` \| `Offline`. The third column is a
metric string (e.g. document count for the Database row); many rows report `"0"`
or `"—"` as placeholders.

```python
import httpx
rows = httpx.get("http://localhost:8000/system/health").json()
ok = all(state == "Healthy" for _name, state, _metric in rows)
```

---

## 3. Documents

Documents are the unit of upload. Each upload creates one document row **and**
one ingest job that runs the OCR → chunk → embed → index pipeline. A document
becomes answerable in chat only once its job reaches `status="RAG READY"`
(`rag="Ready"`).

> **Gotcha — deleting while ingesting doesn't stick.** If you
> [`DELETE`](#delete-documentsdoc_id) a document whose job is still running, the
> worker's later status writes (`PROCESSING`/`RAG READY`/`FAILED`) overwrite the
> `DELETED` status and resurrect the row. Cancel the job (or wait it out) before
> deleting.

### `GET /documents`

List the current user's documents, newest-updated first.

**Query params:** none.

**Response `200`** — `DocumentOut[]`. **Includes soft-deleted rows**
(`status="DELETED"`); filter them client-side if you only want live documents.

```python
docs = httpx.get("http://localhost:8000/documents").json()
live = [d for d in docs if d["status"] != "DELETED"]
ready = [d for d in live if d["status"] == "RAG READY"]
```

### `POST /documents`

Upload one or more files. Each accepted file creates a document **and** an
ingest job. Accepts `multipart/form-data` with a repeated `files` field.

**Constraints:**
- Allowed extensions: `.pdf`, `.png`, `.jpg/.jpeg`, `.webp`, `.bmp`, `.gif`, `.tiff/.tif`.
  Any other extension → `415`.
- PDF page count is read server-side (PyMuPDF); images report `pages: 1`.

**Request** — `multipart/form-data`:

| Field | Type | Notes |
|---|---|---|
| `files` | file (repeated) | One or more uploads. |

```python
import httpx

with open("policy-handbook.pdf", "rb") as f:
    r = httpx.post(
        "http://localhost:8000/documents",
        files={"files": ("policy-handbook.pdf", f, "application/pdf")},
    )
print(r.json())   # {'uploaded': 1, 'status': 'UPLOADED'}
```

**Response `200`** — `{"uploaded": <int>, "status": "UPLOADED"}`.

| Status | When |
|---|---|
| `200` | All files accepted. |
| `415` | An unsupported file extension. |
| `422` | Malformed multipart (no `files`). |

The created document/job ids are **not** returned — poll
[`GET /documents`](#get-documents) / [`GET /jobs`](#get-jobs) to find them by
`name`. (The audit log from [`GET /activity`](#get-activity) also records each
`upload` with its `documentId`.)

### `GET /documents/{doc_id}`

A single document.

**Path params:** `doc_id`.

**Response `200`** — `DocumentOut`. **`404`** if the document does not exist
(or belongs to another user).

```python
doc = httpx.get(f"http://localhost:8000/documents/{doc_id}").json()
```

### `GET /documents/{doc_id}/file`

Download the original uploaded file bytes.

**Path params:** `doc_id`.

**Response `200`** — the file as a binary stream with a safe `Content-Type`
(allowlisted to `application/pdf` + standard image types; anything else is
coerced to `application/octet-stream`, with `X-Content-Type-Options: nosniff`).
**`404`** if the document or its on-disk file is gone (e.g. after soft delete).

```python
with httpx.stream("GET", f"http://localhost:8000/documents/{doc_id}/file") as r:
    with open("download.pdf", "wb") as out:
        for chunk in r.iter_bytes():
            out.write(chunk)
```

### `DELETE /documents/{doc_id}`

Soft-delete a document: wipe its vectors, unlink the stored file, set
`status="DELETED"`. The row is retained (for audit history) and still appears in
[`GET /documents`](#get-documents).

**Response `200`** — `{"id": doc_id, "status": "DELETED"}`. **`404`** if not
found.

```python
httpx.delete(f"http://localhost:8000/documents/{doc_id}")
```

---

## 4. Jobs

Each upload creates one job that runs the ingest pipeline. Jobs queue serially
(one worker, `worker-1`) and can be cancelled, retried, or re-prioritised while
waiting.

### `GET /jobs`

List the current user's jobs.

**Response `200`** — `JobOut[]`.

```python
jobs = httpx.get("http://localhost:8000/jobs").json()
waiting = [j for j in jobs if j["status"] == "WAITING"]
```

### `POST /jobs/{job_id}/cancel`

Request cancellation. The worker checks for cancellation between pipeline
stages (and within the OCR page loop), then finalises the job as `CANCELLED`.

**Response `200`** — `{"id": job_id, "status": "CANCELLED"}`.

> Cancellation is **cooperative**. A running `OCR Processing` stage is
> interrupted within one page; other stages finish their current step first.
> Until the worker acts on it, the job still reports its prior status.

```python
httpx.post(f"http://localhost:8000/jobs/{job_id}/cancel")
```

### `POST /jobs/{job_id}/retry`

Re-queue a finished/failed/cancelled job for another run. Resets
`status="WAITING"`, `stage="Waiting"`, `progress=0`.

**Response `200`** — `{"id": job_id, "status": "WAITING"}`.

```python
httpx.post(f"http://localhost:8000/jobs/{job_id}/retry")
```

### `PATCH /jobs/{job_id}/priority`

Set a waiting job's priority to `Normal` or `Urgent`.

**Request body:**

```json
{ "priority": "Urgent" }
```

**Response `200`** — the updated `JobOut`. **`404`** if the job does not exist.
**`409`** (`"job is no longer waiting"`) if the job has already started or
finished — priority only matters while queued.

```python
r = httpx.patch(f"http://localhost:8000/jobs/{job_id}/priority",
                json={"priority": "Urgent"})
print(r.json()["priority"])   # 'Urgent'
```

---

## 5. Chat & Conversations

This is the core of the platform. [`POST /chat`](#post-chat) answers a question
grounded in the indexed documents and **streams** the answer over SSE; the
conversation endpoints let you list, read, edit-resend, rename, rescope, and
delete conversations.

### `POST /chat`

Ask one question, optionally continuing an existing conversation. Returns an SSE
stream — see the [SSE primer](#server-sent-events-primer-the-chat-stream).

**Request body** — `ChatRequest`:

| Field | Type | Required | Notes |
|---|---|---|---|
| `question` | string | yes | Max 4000 chars. |
| `scope` | `KnowledgeScope` | yes | `{"mode": "all"\|"selected", "documentIds": [...]}`. **The scope in the request body is what retrieval uses for that turn** — it is not read from the stored conversation. |
| `conversationId` | string \| null | no | Omit/`null` starts a new conversation; pass an existing id to continue. |

**Response** — `text/event-stream` of `delta` then `done` events. The HTTP
status is `200`; there is no JSON body. If `conversationId` refers to a
nonexistent conversation, the response is a normal `404` JSON error (the stream
never starts).

> **Important behaviors**
> - The user message is persisted **before** streaming begins, and the assistant
>   message is persisted in a `finally` block — so even an errored or cancelled
>   turn leaves both rows in history.
> - When the turn overflows the conversation's verbatim memory window, the server
>   schedules a best-effort background task to fold older messages into a running
>   summary. See [Scenario 5](#scenario-5--long-conversations--memory).

```python
done = chat("http://localhost:8000", {          # the helper from the SSE primer
    "question": "What is the remote-work policy?",
    "scope": {"mode": "all", "documentIds": []},
    "conversationId": None,                     # start fresh
})
print(done["conversationId"])                   # keep this for the next turn
print(done["state"], len(done["citations"]))
```

For a complete multi-turn walkthrough, see
[§9](#9-multi-turn-conversation-deep-dive).

### `GET /conversations`

List the current user's conversations, most-recently-updated first.

**Response `200`** — `ConversationOut[]`.

```python
convs = httpx.get("http://localhost:8000/conversations").json()
```

### `GET /conversations/{conversation_id}/messages`

Full message history of one conversation, oldest first.

**Path params:** `conversation_id`.

**Response `200`** — `ConversationMessageOut[]`. **`404`** if the conversation
does not exist.

```python
msgs = httpx.get(f"http://localhost:8000/conversations/{conv_id}/messages").json()
for m in msgs:
    print(m["role"], "→", m["content"][:80])
```

### `DELETE /conversations/{conversation_id}/messages/{message_id}`

**Edit-resend support.** Deletes `message_id` **and every message after it** in
the same conversation (by `created_at`). You then re-[`POST /chat`](#post-chat)
with the corrected question and the same `conversationId` to regenerate the
tail.

Only **user** messages may be the truncation anchor, and only ones that have
**not** already been folded into the conversation summary.

**Path params:** `conversation_id`, `message_id`.

| Status | When |
|---|---|
| `200` | Truncated. Body: `{"id": message_id, "status": "DELETED"}`. |
| `400` | `message_id` is not a user message (`"only user messages can be edited"`). |
| `404` | Conversation or message not found. |
| `409` | The message is below the summary fold line (`"message is already summarized and can no longer be edited"`). |

```python
httpx.delete(f"http://localhost:8000/conversations/{conv_id}/messages/{user_msg_id}")
```

See [Scenario 4](#scenario-4--edit-resend-a-turn) for the full edit-resend flow.

### `PATCH /conversations/{conversation_id}`

Update a conversation's title and/or its **stored** scope. Either field is
optional; send only what you want to change.

**Request body** — `UpdateConversationRequest`:

| Field | Type | Notes |
|---|---|---|
| `title` | string \| null | `min_length=1, max_length=200`. |
| `scope` | `KnowledgeScope` \| null | Updates the stored scope (display/metadata). |

**Response `200`** — the updated `ConversationOut`. **`404`** if not found.

> Remember: the **stored** scope is metadata. Per-turn retrieval always uses the
> `scope` in the [`POST /chat`](#post-chat) request body, not this stored value.

```python
httpx.patch(f"http://localhost:8000/conversations/{conv_id}",
            json={"title": "Remote-work policy Q&A"})
```

### `DELETE /conversations/{conversation_id}`

Permanently delete a conversation and all of its messages (hard delete, unlike
documents).

**Response `200`** — `{"id": conversation_id, "status": "DELETED"}`. **`404`**
if not found.

```python
httpx.delete(f"http://localhost:8000/conversations/{conv_id}")
```

---

## 6. Settings

Per-user chat overrides (model, system prompt, temperature). Any field set to
`null` means "use the global default". Retrieval/answering reads the **effective**
settings (override-or-default) on every [`POST /chat`](#post-chat).

### `GET /settings/chat`

**Response `200`**:

```json
{
  "chatModel": "gpt-oss:120b",
  "systemPrompt": "You are the offline knowledge assistant…",
  "temperature": 0.2,
  "defaults": {
    "chatModel": "gpt-oss:120b",
    "systemPrompt": "You are the offline knowledge assistant…",
    "temperature": 0.2
  }
}
```

The top-level fields are the **effective** values (your override, else default);
`defaults` is the global fallback, so a UI can offer "reset to default".

```python
s = httpx.get("http://localhost:8000/settings/chat").json()
print(s["chatModel"], s["temperature"])
```

### `PUT /settings/chat`

Set per-user overrides. Send `null` for any field to clear the override and fall
back to the default.

**Request body** — `ChatSettings`:

```json
{ "chatModel": "gpt-oss:120b", "systemPrompt": null, "temperature": 0.3 }
```

`temperature` (when not null) must be in `[0, 2]`.

**Response `200`** — `{"ok": true}`. **`422`** on validation failure
(e.g. `temperature` out of range).

```python
httpx.put("http://localhost:8000/settings/chat",
          json={"temperature": 0.3})
```

### `GET /settings/models`

List model names available on the Ollama host (for populating a model dropdown).

**Response `200`** — `{"models": ["gpt-oss:120b", "bge-m3:latest", …]}`. If the
Ollama host is unreachable, returns `{"models": []}` (never errors).

```python
models = httpx.get("http://localhost:8000/settings/models").json()["models"]
```

---

## 7. OpenAI-compatible API (`/v1`)

The platform exposes an OpenAI-compatible API at `/v1` — any OpenAI SDK or
client can use the knowledge base by pointing at this server with an API key.

A machine-readable OpenAPI schema is served live by the server at
`/openapi.json`, with interactive exploration at `/docs` (both linked from
Settings → External API). This section is the hand-written wire reference for
the external surface.

### Authentication

**All `/v1/*` endpoints require the platform API key.** Generate it in the web UI
at **Settings → External API**, then pass it via the `Authorization` header:

```bash
Authorization: Bearer <your-api-key>
# or: X-API-Key: <your-api-key>
```

Without the key, requests return `401 Unauthorized`.

### `GET /v1/models`

List the available model(s). The RAG platform advertises a single model:
`rag-grounded` (the grounded chat model).

**Response `200`** — OpenAI `Models` shape:

```json
{
  "object": "list",
  "data": [
    {
      "id": "rag-grounded",
      "object": "model",
      "created": 1724659200,
      "owned_by": "rag-platform"
    }
  ]
}
```

```python
import httpx
models = httpx.get(
    "http://localhost:8000/v1/models",
    headers={"Authorization": "Bearer your-key"}
).json()
print([m["id"] for m in models["data"]])  # ['rag-grounded']
```

### `POST /v1/chat/completions`

Chat completions with RAG grounding. Supports both streaming and non-streaming
modes; the `model` field is optional and accepted leniently — the platform serves
the single model `"rag-grounded"`.

**Authentication:** `Authorization: Bearer <api-key>` header (required).

**Request body** — OpenAI `ChatCompletionRequest` shape (relevant fields):

```jsonc
{
  "model": "rag-grounded",           // optional; accepted leniently
  "messages": [
    {"role": "user", "content": "your question"}
  ],
  "stream": false,                   // optional; default false
  "grounding_footer": true          // optional; default true — appends "Sources:" footer
}
```

- `model` is optional and accepted leniently (the platform serves a single model).
- `messages` must contain at least one message. **All messages before the last are
  treated as conversation history** (system messages are preserved after the
  platform's grounding prompt). **The last message must have `role: "user"`** →
  `400` if violated.
- `stream` controls whether the response is JSON (`false`) or SSE (`true`).
- `grounding_footer` controls whether a markdown "Sources:" footer is appended
  to the content when citations exist.

#### Non-streaming response

**Response `200`** — OpenAI `ChatCompletion` shape with RAG extensions:

```json
{
  "id": "chatcmpl_abc123",
  "object": "chat.completion",
  "created": 1724659200,
  "model": "rag-grounded",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Employees may work remotely up to 3 days per week…\n\n---\n**Sources:**\n[1] policy-handbook.pdf (page 4)"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 52,
    "completion_tokens": 38,
    "total_tokens": 90
  },
  "citations": [
    {
      "number": 1,
      "documentId": "doc_abc123",
      "documentName": "policy-handbook.pdf",
      "page": 4,
      "excerpt": "Employees may work remotely up to 3 days/week…"
    }
  ],
  "grounded": true
}
```

**RAG extensions** (beyond standard OpenAI fields):

| Field | Meaning |
|---|---|
| `citations` | Source passages referenced in the answer. Shape: `{number, documentId, documentName, page, excerpt}` — no internal `id` field. |
| `grounded` | `true` if the answer cited at least one retrieved passage; `false` if the model answered from general knowledge. |

**`usage` note:** Token counts are approximate (chars ÷ 4) and informational only. The `content` field includes the "Sources:" footer when `grounding_footer=true` and citations exist.

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-key"
)
resp = client.chat.completions.create(
    model="rag-grounded",
    messages=[{"role": "user", "content": "What is the remote-work policy?"}]
)
print(resp.choices[0].message.content)
print(resp.grounded, len(resp.citations))
```

#### Streaming response

Set `"stream": true` to receive Server-Sent Events (`text/event-stream`). The
format follows OpenAI's SSE conventions:

```
data: {"id":"chatcmpl_…","object":"chat.completion.chunk","created":1724659200,"model":"rag-grounded","choices":[{"index":0,"delta":{"content":"Employees "},"finish_reason":null}]}

data: {"id":"chatcmpl_…","object":"chat.completion.chunk","created":1724659200,"model":"rag-grounded","choices":[{"index":0,"delta":{"content":"may work "},"finish_reason":null}]}

…

data: {"id":"chatcmpl_…","object":"chat.completion.chunk","created":1724659200,"model":"rag-grounded","choices":[{"index":0,"delta":{"content":"\n\n---\n**Sources:**\n[1] policy-handbook.pdf (page 4)"},"finish_reason":null}]}

data: {"id":"chatcmpl_…","object":"chat.completion.chunk","created":1724659200,"model":"rag-grounded","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"citations":[{"number":1,"documentId":"doc_abc123","documentName":"policy-handbook.pdf","page":4,"excerpt":"Employees may work remotely up to 3 days/week…"}],"grounded":true}

data: [DONE]
```

- Concatenate `choices[0].delta.content` in order to reconstruct the answer.
- The "Sources:" footer (when `grounding_footer=true` and citations exist) is streamed
  as a content chunk before the final chunk.
- The final chunk has `"finish_reason": "stop"`, an empty `delta`, **and includes**
  `citations` and `grounded` fields.
- `[DONE]` signals stream end (OpenAI convention).

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-key"
)
stream = client.chat.completions.create(
    model="rag-grounded",
    messages=[{"role": "user", "content": "What is the remote-work policy?"}],
    stream=True
)
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

#### Error responses

| Status | When | Body shape |
|---|---|---|
| `401` | Missing or invalid API key. | OpenAI-shaped `{"error": {"message": "…", "type": "invalid_request_error"}}` |
| `400` | Invalid request semantics (e.g. last message not role "user", empty user message). | OpenAI-shaped error |
| `502` | Upstream LLM or embedding failure (Ollama unreachable). | OpenAI-shaped error |
| `422` | Pydantic validation failure (malformed JSON). | **FastAPI shape** `{"detail": [...]}` — this diverges from OpenAI; 422 never returns an OpenAI-shaped error |

> **Validation deviation.** FastAPI's built-in validation returns FastAPI's 422 shape,
> not the OpenAI error object. All other errors (401/400/502) follow the OpenAI
> format with `{message, type, code}` fields.

---

## 8. Search (public)

### `POST /search`

**Retrieval-only** — no LLM call. Runs the same embedding + vector search as
chat and returns the raw ranked chunks, so another program can feed them into
its own model.

**Authentication:** now requires the platform API key (same as `/v1`). Pass it
via `X-API-Key` header or `Authorization: Bearer`:

```bash
curl -X POST http://localhost:8000/search \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"question":"remote-work policy","scope":{"mode":"all","documentIds":[]}}'
```

Without the key, requests return `401 Unauthorized`.

**Request body** — same `ChatRequest` shape as `/chat` (`question` + `scope`;
`conversationId` is accepted but ignored).

**Response `200`**:

```json
{
  "query": "What is the remote-work policy?",
  "results": [
    {
      "documentId": "doc_abc123",
      "documentName": "policy-handbook.pdf",
      "page": 4,
      "score": 0.612,
      "excerpt": "Employees may work remotely up to 3 days/week…"
    }
  ]
}
```

- Top `RAG_TOP_K` hits (default 12; same `k` as `/chat` retrieval). **No
  minimum-score filtering** — unlike `/chat`,
  `/search` returns all ranked chunks regardless of score, so the caller can
  apply its own threshold from the returned `score`.
- `mode: "selected"` restricts to the given `documentIds`; `mode: "all"`
  searches every `RAG READY` document.
- `excerpt` is the first 240 characters of the chunk.

```python
r = httpx.post(
    "http://localhost:8000/search",
    headers={"X-API-Key": "your-key"},
    json={
        "question": "remote-work policy",
        "scope": {"mode": "all", "documentIds": []},
    }
)
for hit in r.json()["results"]:
    print(hit["score"], hit["documentName"], "p.", hit["page"])
```

---

## 9. Activity

### `GET /activity`

The user's audit log — uploads and deletes, most recent first (capped at 100).

**Response `200`**:

```json
[
  { "action": "upload", "documentId": "doc_abc123", "detail": "policy-handbook.pdf", "ts": "2026-08-10 09:30:11" },
  { "action": "delete", "documentId": "doc_def",    "detail": "old-draft.pdf",      "ts": "2026-08-09 17:02:00" }
]
```

`action` is currently `upload` \| `delete`.

```python
activity = httpx.get("http://localhost:8000/activity").json()
```

---

## 10. Multi-turn conversation deep-dive

This section is the heart of the manual. Conversations are first-class: the
server remembers recent turns verbatim, folds older turns into a running
summary, rewrites follow-ups into standalone retrieval queries, and supports
edit-resend. Below are six end-to-end scenarios with real payloads and Python
client code.

**Setup used by every scenario** — install `httpx`, then reuse the `chat()`
helper from the [SSE primer](#server-sent-events-primer-the-chat-stream):

```python
import json, httpx

BASE = "http://localhost:8000"

def chat(question, conv_id=None, scope=None, verbose=True):
    payload = {
        "question": question,
        "scope": scope or {"mode": "all", "documentIds": []},
        "conversationId": conv_id,
    }
    parts, done, event = [], None, None
    with httpx.stream("POST", f"{BASE}/chat", json=payload, timeout=None) as r:
        for line in r.iter_lines():
            if not line:
                continue
            field, _, value = line.partition(": ")
            if field == "event":
                event = value
            elif field == "data":
                data = json.loads(value)
                if event == "delta":
                    parts.append(data["text"])
                    if verbose:
                        print(data["text"], end="", flush=True)
                elif event == "done":
                    done = data
    if verbose:
        print()
    done["_answer"] = "".join(parts)
    return done
```

---

### Scenario 1 — Start a conversation

**Goal.** Ask the first question against the knowledge base and obtain the
`conversationId` to continue with.

**What happens server-side.** With `conversationId: null`, `/chat` creates a new
conversation row titled with the first 60 characters of the question, persists
the user message, runs retrieval+generation, streams `delta`s, then emits
`done`. The `conversationId` you need is in the `done` event.

**Request.**

```python
done = chat("What is the remote-work policy?")
conv_id = done["conversationId"]          # e.g. "conv_01J…"
print("state     :", done["state"])        # 'supported'
print("citations :", [c["number"] for c in done["citations"]])
```

**Live stream the client sees:**

```
event: delta
data: {"text": "Employees may work remotely up to 3 days per week [1]. "}

event: delta
data: {"text": "Manager approval is required for additional days."}

event: done
data: {"citations": [{"id":"cite-1","number":1,"documentId":"doc_abc123","documentName":"policy-handbook.pdf","page":4,"excerpt":"Employees may work remotely up to 3 days/week…"}], "state":"supported", "conversationId":"conv_01J…", "userMessageId":"msg_01J…"}
```

**Takeaway:** the answer text lives only in the `delta` stream; `done` carries
metadata + the *referenced* citations (passage `[1]` was cited, so it appears;
uncited passages do not).

---

### Scenario 2 — Continue it (an N-turn loop)

**Goal.** Have a real back-and-forth where each follow-up depends on the
previous answer, e.g. *“What is the remote-work policy?” → “And how do I
request it?” → “What's the approval SLA?”*.

**What happens server-side on each continuation.** Passing the `conversationId`
back makes `/chat`:
1. Load **memory** for the conversation: a running **summary** of old turns plus
   the last **6 messages** (3 user/assistant pairs — `CHAT_VERBATIM_PAIRS=3`)
   kept **verbatim**.
2. **Condense** the new follow-up into a standalone retrieval query using that
   verbatim history (so *“And how do I request it?”* becomes something like
   *“How do I request remote work?”* — retrieving the right passages even though
   the follow-up alone has no noun).
3. Retrieve, generate, stream, persist — exactly like turn 1.

**Request — a turn-taking loop.**

```python
conv_id = chat("What is the remote-work policy?")["conversationId"]

followups = [
    "And how do I request it?",     # resolved via condensed query + history
    "What is the approval SLA?",
    "Does any of that change for contractors?",
]
for q in followups:
    done = chat(q, conv_id=conv_id)
    # done["state"], done["citations"], done["_answer"] are all available
```

**Why the condensation step matters (visible effect).** Ask *“And how do I
request it?”* with **no** `conversationId` (a brand-new conversation) and
retrieval has nothing to resolve “it” to — you'll typically get a vaguer answer
or `state: "no-result"`. Ask the identical question **with** the `conversationId`
and the condensed query targets the request procedure, grounded in the same
passages turn 1 used. The conversation id is what carries the pronoun.

**Inspecting history between turns.**

```python
msgs = httpx.get(f"{BASE}/conversations/{conv_id}/messages").json()
print(len(msgs), "messages so far")
# roles alternate: user, assistant, user, assistant, …
```

---

### Scenario 3 — Scope & named-document targeting

**Goal.** Restrict an answer to a subset of documents, or point a question at a
specific file by naming it.

**Two scope mechanisms (per turn, via the request body):**

1. **Explicit scope** — `{"mode": "selected", "documentIds": [id, …]}` restricts
   retrieval to exactly those documents. Get the ids from
   [`GET /documents`](#get-documents) (filter `status == "RAG READY"`).
2. **Named-document detection** — in `mode: "all"`, if the question text
   contains a document's full filename (e.g. *“In `q3-report.pdf`, what was
   revenue?”*) or an unambiguous filename stem, retrieval auto-targets that
   document. Ambiguous or absent names fall back to searching all documents.

> **Edge case.** `mode: "selected"` with an **empty** `documentIds` list is
> falsy, so the server falls through to all-documents behaviour (including
> named-document detection). If you genuinely want "selected, nothing", that is
> indistinguishable from "all" here — prefer `mode: "all"` to avoid surprise.

**Request — selected scope.**

```python
docs = [d for d in httpx.get(f"{BASE}/documents").json()
        if d["status"] == "RAG READY"]
ids = [d["id"] for d in docs if "handbook" in d["name"].lower()]

done = chat("Summarise the leave policy", scope={"mode": "selected", "documentIds": ids})
```

**Request — named-document targeting (mode: all).**

```python
done = chat("In policy-handbook.pdf, what is the remote-work policy?",
            scope={"mode": "all", "documentIds": []})
# retrieval is auto-restricted to policy-handbook.pdf because its name is in the question
```

If a named query returns nothing above the minimum score, the server keeps that
document's **top 3** passages anyway rather than answering empty-handed — useful
to know when an answer looks weakly grounded.

---

### Scenario 4 — Edit-resend a turn

**Goal.** The user misspoke in an earlier turn and wants to change that question
and regenerate everything that came after it — without losing the turns before.

**Mechanism.** Conversations are append-only by `created_at`; the edit flow is:
1. Find the user message to edit in
   [`GET /conversations/{id}/messages`](#get-conversationsconversation_idmessages).
2. [`DELETE`](#delete-conversationsconversation_idmessagesmessage_id) it — this
   removes that user message **and every later message** (its answer and all
   subsequent turns).
3. [`POST /chat`](#post-chat) again with the corrected question and the **same**
   `conversationId`. The new turn is appended where the old tail was.

**Request.**

```python
conv_id = "<existing conversation>"

# 1. read history, find the user turn to fix
msgs = httpx.get(f"{BASE}/conversations/{conv_id}/messages").json()
target = next(m for m in msgs if m["role"] == "user"
              and "remot work" in m["content"])     # the typo'd question
user_msg_id = target["id"]

# 2. truncate from that message onward
httpx.delete(f"{BASE}/conversations/{conv_id}/messages/{user_msg_id}")

# 3. re-ask with the corrected question
done = chat("What is the remote-work policy?", conv_id=conv_id)
```

**Status codes to expect on the `DELETE`:**

| Outcome | Status | Body |
|---|---|---|
| Truncated cleanly | `200` | `{"id": …, "status": "DELETED"}` |
| `message_id` is an assistant message | `400` | `{"detail": "only user messages can be edited"}` |
| Conversation/message unknown | `404` | `{"detail": "…"}` |
| Message is already in the summary | `409` | `{"detail": "message is already summarized and can no longer be edited"}` |

**The `409` case (the summary fold line).** Once a conversation grows beyond the
6-message verbatim window, the oldest turns are folded into a summary
([Scenario 5](#scenario-5--long-conversations--memory)). Folded messages can no
longer be edited — truncating them would leave the summary referencing deleted
content. You can still edit any **recent** (un-folded) user message. There is no
"un-summarise" operation; if you must revise an old turn, start a new
conversation.

---

### Scenario 5 — Long conversations & memory

**Goal.** Understand how a 20-turn conversation stays coherent (and cheap) when
only 6 messages fit in the prompt.

**Memory model** (per turn, server-side):

- The prompt always includes the **last 6 messages verbatim** (3 user + 3
  assistant, `CHAT_VERBATIM_PAIRS=3`).
- Messages **older** than that window are folded into a single running
  `summary` stored on the conversation row. That summary is injected as a system
  message, so the model still "remembers" the gist of early turns.
- The fold is triggered automatically: after any turn that pushes the message
  count past the window, `/chat` schedules a **background** summarisation task.
  It is best-effort — if it fails, nothing breaks; the next overflowing turn
  retries it.

**What this means for the API consumer:**
- You do **not** send history in the request — the server reconstructs it from
  the stored messages. Just send `question` + `conversationId`.
- [`GET /conversations/{id}/messages`](#get-conversationsconversation_idmessages)
  always returns the **full** stored history (the summary is internal; folded
  messages are not deleted, just not re-sent verbatim to the model).
- A turn that lands **during** the brief window before the background fold runs
  still answers correctly — it just sends a slightly larger verbatim set until
  the fold catches up.

**Citations across long conversations.** Citation numbers `[n]` are
**per-turn**, scoped to that turn's retrieved passages — `[1]` in turn 2 is a
different passage from `[1]` in turn 8. The `done.citations` for each turn and
the `citations` on each stored assistant message always refer to that single
turn's `[n]` numbering. Don't try to merge citation numbers across turns.

**Observing the fold.** Over a long loop you can watch the conversation grow
while the model keeps earlier context via the summary:

```python
conv_id = chat("Let's audit the whole handbook, section by section.")["conversationId"]
for section in ["leave", "remote work", "expenses", "code of conduct", "security"]:
    chat(f"Summarise the {section} section.", conv_id=conv_id)

n = len(httpx.get(f"{BASE}/conversations/{conv_id}/messages").json())
print(n, "messages stored")   # keeps growing; the model sees summary + last 6
```

---

### Scenario 6 — Failure & cancellation states

**Goal.** Handle the four `done.state` values and client-side cancellation
correctly.

| `state` | When it happens | What's in the stream |
|---|---|---|
| `supported` | The model returned a **non-empty** answer — the common case. This does **not** by itself mean the answer was grounded in the documents (see the note below the table). | `delta`s + `done`. `citations` is non-empty only if the answer actually cited a retrieved passage. |
| `no-result` | The model returned an **empty** answer (it declined to say anything). Rare in practice — see the note below: a below-threshold retrieval usually yields `supported` with `citations=[]`, not `no-result`. | No `delta`s; `done` with `state: "no-result"`, empty `citations`. |
| `error` | The LLM call failed, **or** something broke before streaming (embedding/retrieval). | Possibly some `delta`s (partial); `done` with `state: "error"`, empty `citations`. |
| `cancelled` | The client disconnected before the `done` tuple was produced. | Whatever `delta`s streamed before disconnect. The server finalises and **persists** the turn as `cancelled`; a final `done` is emitted, but the cancelling client may not receive it (its connection is already closed). The `cancelled` state is still visible via `GET /conversations/{id}/messages`. |

> **`supported` ≠ grounded.** `state` only signals whether the model emitted
> answer text (`backend/rag.py` sets `"supported" if ans else "no-result"`). The
> reliable signal that an answer is actually grounded in the indexed documents
> is a **non-empty `citations` list** — the server keeps only the passages the
> answer marked `[n]`. When retrieval finds nothing above `RAG_MIN_SCORE`, the
> system prompt lets the model answer from its own general knowledge (with an
> in-answer disclaimer), so you typically get `state="supported"` with
> `citations=[]` — detect "not in the docs" by checking `citations`, not `state`.

**Important:** the assistant message is **always** persisted (in a `finally`
block), so an `error`/`cancelled` turn still appears in history with its state
recorded. When you replay history, render these states distinctly (e.g. show an
error badge) rather than treating them as normal answers.

**Client-side cancellation** (e.g. a "Stop" button) is just closing the stream:

```python
import httpx

with httpx.stream("POST", f"{BASE}/chat", json=payload, timeout=None) as r:
    try:
        for line in r.iter_lines():
            if line.startswith("data: "):
                # …render tokens…
                pass
            if user_pressed_stop():          # your UI signal
                break                         # closing the context manager ends the request
    finally:
        pass
# server observes the disconnect and finalises the turn with state: "cancelled"
```

**Recovering from an error turn.** Because the failed turn is in history, the
cleanest recovery is an [edit-resend](#scenario-4--edit-resend-a-turn): delete
the failed user message (which also drops its error assistant reply) and re-ask.
Or simply continue with a new follow-up — the model will see the failed turn in
its verbatim window, which is usually fine but can occasionally confuse
condensation; edit-resend is the deterministic fix.

---

## 11. Appendix

### Error catalog

| Status | Meaning | Where |
|---|---|---|
| `200` | Success (JSON body, or SSE/binary stream). | everywhere |
| `400` | Bad request semantics — e.g. editing a non-user message, last message not role "user" in `/v1/chat/completions`. | `DELETE …/messages/{id}`, `/v1/*` |
| `401` | Missing or invalid API key (`/v1/*`, `/search`). | `/v1/*`, `POST /search` |
| `404` | Resource not found / not owned by the user / on-disk file missing. | most routes |
| `409` | Conflict — e.g. setting priority on a non-waiting job, or editing an already-summarised message. | `PATCH /jobs/{id}/priority`, `DELETE …/messages/{id}` |
| `415` | Unsupported file extension on upload. | `POST /documents` |
| `422` | Pydantic validation failure — e.g. `question` over 4000 chars, `temperature` out of `[0,2]`, `title` outside 1–200, malformed multipart. | body-bearing routes |
| `502` | Upstream failure (Ollama/embedding unreachable). | `/v1/chat/completions` |
| `200` + `state: "error"\|"cancelled"\|"no-result"` | Application-level chat failure delivered **inside** a successful `200` SSE stream. | `POST /chat` |

### Default configuration

Defaults come from environment variables (shown). The values that most affect
API behaviour:

| Setting | Default | Effect |
|---|---|---|
| `CHAT_MODEL` | `gpt-oss:120b` | Model used to answer `/chat`. Override per-user via [`PUT /settings/chat`](#put-settingschat). |
| `EMBED_MODEL` | `bge-m3:latest` | Embedding model for retrieval (`/chat`, `/search`). |
| `OCR_MODEL` | `scb10x/typhoon-ocr-7b:latest` | Model used by the ingest OCR stage. |
| `CHAT_TEMPERATURE` | `0.2` | Generation temperature. |
| `CHAT_VERBATIM_PAIRS` | `3` | Verbatim window = this × 2 messages (default 6). |
| `RAG_MIN_SCORE` | `0.35` | Minimum retrieval score to count a passage as relevant. |
| `DEMO_USER_ID` | `usr_demo` | The single (no-auth) user identity. |

All models are served by the **Ollama host** (`OLLAMA_HOST`); vectors live in
**Qdrant** (`QDRANT_URL`, collection `rag_chunks`).
