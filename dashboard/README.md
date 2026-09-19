# ONION-Q — Centre Dashboard

A single static page (`index.html`) — no build step, no framework, no npm.

## Run

```bash
# 1. start the API
uvicorn server.app:app --port 8000

# 2. serve the dashboard
python -m http.server 8081 --directory dashboard
# open http://127.0.0.1:8081
```

## Views

| Panel | Source | Notes |
|---|---|---|
| Inspection KPIs | `GET /dashboard/summary` | Reports synced, onions scanned, graded, grade-A / relaxed / reject / manual-review shares, mean model confidence, override rate |
| Grade distribution | same | Bars over the decision counts, with the percentage denominator stated underneath |
| Manual-review and defect reasons | same | Reason-code histogram (plain-language text in `src/common/reasons.py`) |
| Centre comparison | same (`by_center`) | Graded count and grade-A share per centre — no cross-centre ranking is implied from small samples |
| Trend by date | same (`by_date`) | Last 14 report dates: graded, grade A, manual review |
| Human-in-the-loop | `GET /dashboard/overrides` | Override count, agreement/disagreement with the AI, disagreement rate, reasons, per-model breakdown |
| Recent batches | `GET /dashboard/scans` + `GET /report/verify/{id}` | Integrity is re-computed per report and shown as *hash matches* or **HASH MISMATCH**; every row is labelled **DEMO** |
| Data provenance | `GET /models` | Model ids, tasks, artifacts and `metrics_confidence` — including which artifacts are absent |

## Demo labelling

A banner and a per-row `DEMO` pill state that the figures come from locally
stored demonstration reports. No official, national or NAFED statistic is shown
or implied, and there is no synthetic filler data.

## Deliberate absence

There is **no** "accuracy" or "confidence trend" widget, because those numbers
would have to be invented: the dashboard shows only counts and reason codes that
were actually recorded in the field, plus the model provenance the registry can
prove.
