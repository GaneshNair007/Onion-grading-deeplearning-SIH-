# Procurement Policy Sources — Research Record

**Research date:** 2026-09-18
**Status: NO POLICY IN THIS REPOSITORY IS OFFICIALLY VERIFIED.**
Every shipped policy file carries `"source_verified": false`.

## Why this file exists

The task statement is explicit: do not fabricate government standards. Onion
procurement specifications have also **changed repeatedly in the recent past**
(Grade-A diameter was relaxed to 35–70 mm and later withdrawn), which is
precisely why ONION-Q puts the standard in a versioned config file instead of
inside the model.

## What the search established (context only — press reporting)

| Fact | Source (press) | Access date | Confidence |
|---|---|---|---|
| Grade-A onions were reported as 45–65 mm diameter for buffer-stock procurement | Times of India, Nashik (30 Jul 2026): "only onions measuring 45-65mm and meeting Grade-A standards will be eligible for procurement" | 2026-09-18 | Medium — press only |
| Grade-A specification was **relaxed** to 35–70 mm in June 2026 to speed procurement | Hindustan Times, Pune (4 Jun 2026) | 2026-09-18 | Medium — press only |
| **URS = "Under Relaxed Specifications"** is a real procurement class distinct from Grade A | Rediff/Money (24 Jun 2026): agencies "essentially limited to URS ... since most of the Grade-A produce" was priced out | 2026-09-18 | Medium — press only |
| Centre procures onion buffer stock via NAFED/NCCF with quality verification at CWC warehouses | Indian Express (14 May 2026) | 2026-09-18 | Medium — press only |

URLs are recorded in `config/grading/demo_policy.json` under `context_urls`.

## What this means for the software

1. **Never hard-code a standard into model weights.** The model outputs
   measurements; `src/grading/policy.py` applies the thresholds; every
   decision stores the `policy_id` + `policy_hash` used.
2. **URS must remain a configurable class, not a permanent label.** Both
   `demo_policy.json` (strict, 45–65 mm) and the `relaxed` rule-set inside it
   (35–70 mm) exist so the same measurements can be re-evaluated under either
   standard — the WOW-6 demonstration ("change policy without retraining").
3. **Press reporting is not an official specification.** To promote a policy
   to verified status, the team must obtain an official document (ministry
   order, NAFED/NCCF tender specification, PSF/price-stabilisation fund
   procurement circular), record its reference number and date here, then set
   `source_verified: true`.

## Promotion checklist (before the final demo)

- [ ] Obtain the current official onion procurement specification document.
- [ ] Record: issuing body, document number, publication date, retrieved date.
- [ ] Update `config/grading/*.json` values and set `source_verified: true`.
- [ ] Add a regression test asserting the decision changes for a known
      measurement set between the strict and relaxed policies.
