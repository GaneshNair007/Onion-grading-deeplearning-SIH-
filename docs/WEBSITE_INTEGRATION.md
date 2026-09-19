# Website Integration Guide — the three user cases

This is the exact wiring for the final goal:

1. **Case 1 — Non-onion detection:** user photographs any other vegetable →
   the trained model says *not an onion*.
2. **Case 2 — Onion grading:** user photographs an onion → the trained,
   tested deep-learning pipeline + policy engine return the SIH
   problem-statement grade (Grade A / Relaxed-B / Reject / Manual review).
3. **Case 3 — Acoustic interior check:** the phone is forced to use **its own
   speaker + microphone** (chirp or guided tap), the recording is analysed,
   and the best honestly-trained model reports internal-condition evidence —
   with a clear, permanent honesty label (see §7).

---

## 0. One-time setup (10 minutes)

```bash
# 1. Backend
pip install -r requirements.txt

# 2. Copy env template and edit
cp .env.example .env
#   set: ONIONQ_CORS_ORIGINS=http://localhost:3000   (your website origin)

# 3. Start the API
uvicorn server.app:app --port 8000

# 4. Verify
curl http://127.0.0.1:8000/health
```

Interactive API docs: <http://127.0.0.1:8000/docs>

## 1. Supabase setup (once)

1. Create a project at <https://supabase.com>.
2. SQL Editor → paste the contents of `supabase/schema.sql` → Run.
   (Creates `onion_reports` + `onion_overrides` with public-read RLS;
   writes require the service key.)
3. `.env`:
   ```
   ONIONQ_SUPABASE_URL=https://<project>.supabase.co
   ONIONQ_SUPABASE_SERVICE_KEY=<service_role key>     # server only!
   ONIONQ_SUPABASE_ANON_KEY=<anon key>                # dashboard reads
   ```
4. Push existing local reports:
   ```bash
   curl -X POST http://127.0.0.1:8000/integrations/supabase/push \
        -H "Content-Type: application/json" -d "{}"
   ```
   Or from Python: `python -c "from src.integrations.supabase_sync import sync_reports_dir; print(sync_reports_dir())"`

**Security rule:** the service key lives only in the backend `.env`.
Never ship it to the website bundle; the site talks to the API, the API talks
to Supabase.

## 2. Website → API: the three cases in code

All requests go to the FastAPI server. With CORS configured (§0), the browser
can call it directly; from Node/Next.js call `http://127.0.0.1:8000/...`
server-side to avoid exposing the LAN address.

### Case 1 — non-onion rejection

```js
const form = new FormData();
form.append("image", fileInput.files[0]);
const res = await fetch("http://127.0.0.1:8000/scan/image", {
  method: "POST", body: form,
});
const out = await res.json();
// out.is_onion === false  -> show "Not an onion"
// (detector-gated; falls back to embedding OOD when no detector artifact)
```

### Case 2 — onion grading (SIH problem statement)

```js
const form = new FormData();
form.append("image", fileInput.files[0]);
const res = await fetch("http://127.0.0.1:8000/scan/image", {
  method: "POST", body: form,
});
const out = await res.json();
// out.decision.decision -> "grade_a" | "relaxed" | "reject" | "manual_review"
// out.decision.reasons  -> human-readable rule hits
// Grades come from the versioned policy engine (config/grading/*.json),
// NOT from the neural net — standards can change without retraining.
```

Batch/tray mode (the procurement hero flow): `POST /scan/batch` with a tray
photo → per-onion decisions + batch percentages.

### Case 3 — acoustic interior check (phone speaker + mic)

Mobile web cannot force echo-reference-quality capture; the supported path is
the Android module (`mobile/android/`, see `docs/MOBILE.md`), which uses
`AudioTrack` (speaker) + `AudioRecord` (mic): ambient baseline → chirp (or
guided 3-tap fallback) → WAV. The site receives the finished WAV:

```js
const form = new FormData();
form.append("audio", wavBlob, "tap_response.wav");
const res = await fetch("http://127.0.0.1:8000/acoustic/classify", {
  method: "POST", body: form,
});
const out = await res.json();
// out.status: "valid" | "research_only" | "retest_required"
// Quality gates may demand a RE-test — that is a feature, not a bug.
```

Fusion (vision + acoustic evidence, conservative):

```js
const res = await fetch("http://127.0.0.1:8000/fuse", {
  method: "POST", headers: {"Content-Type": "application/json"},
  body: JSON.stringify({ vision: visionResult, acoustic: acousticResult }),
});
```

## 3. Reading results (canonical contract)

Every endpoint returns the shared contract (`src/common/contracts.py`):

```json
{
  "is_onion": true,
  "vision":   {"label": "sound", "confidence": 0.88, "defects": {}},
  "acoustic": {"status": "research_only", "internal_defect_probability": 0.71,
               "confidence": 0.4},
  "decision": {"decision": "grade_a", "reasons": ["..."]}
}
```

Rule: an acoustic result marked `research_only` can never change the
procurement decision (enforced by tests).

## 4. Persistence & dashboards

- Local/offline-first: `server/store.py` (SQLite) + idempotent `/sync/scans`.
- Cloud: Supabase tables (§1). The website dashboard reads with the anon key
  (public-read RLS) or via the API.

## 5. Endpoint inventory

| Endpoint | Purpose |
|---|---|
| `POST /scan/image` | Case 1 + 2: onion gate → attribute → policy grade |
| `POST /scan/batch` | tray scan: N onions, batch percentages |
| `POST /scan/deep` | 4-view deep scan fusion |
| `POST /acoustic/ambient` | store ambient-noise baseline |
| `POST /acoustic/classify` | Case 3: WAV → quality gates → model |
| `POST /fuse` | vision ⊕ acoustic, conservative |
| `POST /review/override` | inspector override (audit trail) |
| `POST /sync/scans` | offline upload, idempotent by UUID |
| `GET /report/verify/{id}` | tamper-evident report verification |
| `GET /dashboard/summary` | KPIs for the dashboard |
| `POST /integrations/supabase/push` | push reports to Supabase |

## 6. Environment variables

| Var | Purpose |
|---|---|
| `ONIONQ_CORS_ORIGINS` | website origins allowed to call the API |
| `ONIONQ_SUPABASE_URL` | Supabase project URL |
| `ONIONQ_SUPABASE_SERVICE_KEY` | write key — backend `.env` only |
| `ONIONQ_SUPABASE_ANON_KEY` | public dashboard reads |

## 7. Honest status of each case (do not oversell)

| Case | Status | Evidence |
|---|---|---|
| 1. Non-onion rejection | Working on detector gate + embedding OOD; real-world negatives (potato/tomato/hand) not yet collected — false-reject rate unknown | `tests/e2e/test_field_workflow.py::test_non_onion_short_circuits` |
| 2. Onion grading | Working: detector AP50 0.639 (leak-safe), rot F1 0.928, sprout F1 0.784; grades from policy engine; 4-class head research-only | `models/vision/*/model_card.json`, `evaluation/detector_comparison.json` |
| 3. Acoustic interior | Capture + DSP pipeline real; classifier is a synthetic-data demo labelled `research_only` — it CANNOT claim internal-rot detection until real cut-open-labelled onions exist | `dataset-acoustic/README.md`, enforced by tests |

This table is the difference between a defensible SIH project and a
disqualified one. Keep it true.
