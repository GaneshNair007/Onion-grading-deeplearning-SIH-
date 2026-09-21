# Acoustic Data Sources

Every acoustic-related source investigated for this project, with its
verification status. Download date for all entries: 2026-09-18 (search date;
see per-item notes). Nothing here is invented; absent fields are marked
"none found".

## Summary table

| # | Source | Type label | Onion-specific? | Downloadable data? | Redistributed here? |
|---|---|---|---|---|---|
| 1 | Landahl et al. 2022 — onion LDV vibrometry | `paper_only` | **Yes** | Paper **yes** (CC BY 4.0 OA); **raw vibration data: no** | Paper copy redistributable; **not committed yet** — fetch via browser (see entry 1) |
| 2 | Caladcad et al. 2023 — coconut tapping acoustic dataset | `related_produce_acoustic` | No | Yes (Mendeley Data) | **No — CC BY-NC-ND + 278 MB single file** |
| 3 | Labanska et al. 2022 — onion electronic nose | `paper_only` | **Yes** (non-acoustic) | No | No — citation only |
| 4 | Nishino et al. 2019 — dual-beam spectral internal onion rot | `paper_only` | **Yes** (non-acoustic) | No | No — citation only |
| 5 | Islam et al. 2018 — review of non-destructive onion quality | `paper_only` | **Yes** (review) | No | No — citation only |

## Detailed entries

### 1. Detection of internal defects in onion bulbs by means of single-point and scanning laser Doppler vibrometry

- **Dataset or paper name:** Landahl, S., et al., *Biosystems Engineering*,
  Volume 221, September 2022, pp. 258–273.
- **Original URL:** <https://www.sciencedirect.com/science/article/pii/S1537511022001660>
  (also indexed at Cranfield University's institutional repository:
  <https://dspace.lib.cranfield.ac.uk/items/8eb70c8d-bbe8-4fc7-bfe7-045062e2b9e2>)
- **DOI:** `10.1016/j.biosystemseng.2022.07.004`
- **License:** **Paper is open access, CC BY 4.0** (Crossref `vor` license + Unpaywall `cc-by` + Semantic Scholar `CCBY`; verified 2026-09-21). Underlying vibration/audio data remains **not published**.
- **Download date:** metadata 2026-09-18; OA status re-verified 2026-09-21 via Crossref/Unpaywall/Semantic Scholar APIs.
- **How to obtain the paper:** publisher OA page <https://doi.org/10.1016/j.biosystemseng.2022.07.004> or the Cranfield submitted-version PDF <https://dspace.lib.cranfield.ac.uk/bitstreams/c76f38c0-7c18-4d3a-a1f3-24fa8f8a418b/download>. Note: Cranfield DSpace blocks non-browser clients (HTTP 403), so fetch in a normal browser and save as `dataset-acoustic/research/landahl_2022_onion_ldv_paper.pdf` (CC BY permits this and redistribution with attribution). A publisher **Corrigendum** exists: DOI `10.1016/j.biosystemseng.2022.10.012` (Dec 2022) — the user's second reference link; consult alongside the paper.
- **File count / total size:** paper only; underlying vibration/audio data
  **not published** in any public repository found.
- **Audio formats / sample rate:** none published (LDV velocity measurements,
  not air-coupled audio).
- **Labels:** internal defect status of onion bulbs (incl. neck rot),
  established by the authors' destructive/validation procedure.
- **Onion-specific:** **Yes.**
- **Legally redistributable through GitHub:** No (publisher-owned text; no
  dataset published).
- **Known limitations / relevance:** laboratory laser Doppler vibrometry —
  not a phone-only method. The paper demonstrates that onion internal
  defects alter vibration response and stresses controlled acquisition and
  cultivar-aware validation. It is used in this project **only** to design
  the collection protocol (`collection_protocol.md`). It is **not** evidence
  that a phone-microphone model works.
- **Type label:** `paper_only`

### 2. Acoustic Signal Dataset: Tall Coconut Fruit Species (Mendeley Data)

- **Dataset or paper name:** Caladcad, J.A., Piedad, E.J., et al., "Acoustic
  dataset of coconut (*Cocos nucifera*) based on tapping system",
  *Data in Brief* 47:108936 (2023).
- **Original URL:** <https://data.mendeley.com/datasets/hxh8kd3snj/1>
- **DOI:** `10.1016/j.dib.2023.108936` (data brief);
  repository DOI `10.17632/hxh8kd3snj.1`; companion methods paper
  `10.1016/j.compag.2020.105327`.
- **License:** **CC BY-NC-ND 4.0** (stated on the PMC page of the data brief).
- **Download date:** 2026-09-18 (metadata + file listing via Mendeley public
  API; data file itself not downloaded into the repository).
- **File count / total size:** 1 file (`coconut_acoustic signals.xlsx`),
  278,424,725 bytes.
- **Audio formats:** 387 acoustic signals (129 coconuts × 3 ridges) embedded
  in the workbook; per the data brief: raw tapped signals, 16-bit, 44.1 kHz,
  132,300 points per signal (~3 s each).
- **Sample rate:** 44.1 kHz.
- **Labels:** maturity level — `im` premature (8 coconuts), `m` mature (36),
  `om` overmature (85); assigned by local farmers/experts.
- **Onion-specific:** **No** — coconut maturity.
- **Legally redistributable through GitHub:** **No.** CC BY-NC-ND prohibits
  derivative works, and repacking the XLSX into parts would be a derivative;
  additionally the single file exceeds GitHub's 100 MB limit.
- **Known limitations:** coconut, not onion; NoDerivatives; signals embedded
  in XLSX rather than standalone WAVs; heavy class imbalance (8/36/85).
  Useful locally (NonCommercial) for pipeline benchmarking and as a
  methodological template for our own collection protocol.
- **Type label:** `related_produce_acoustic`

### 3. Preliminary studies on detection of *Fusarium basal rot* in onion using an electronic nose

- **Dataset or paper name:** Labanska, M., et al., *Sensors* 22(14):5453 (2022).
- **Original URL:** <https://www.mdpi.com/1424-8220/22/14/5453>
- **DOI:** not recorded (available on the article page).
- **License:** article is open access (MDPI); underlying sensor data
  availability not established during this search.
- **Relevance:** onion-specific but **non-acoustic** (volatile sensing);
  recorded to document that onion internal-rot sensing literature exists
  beyond vibrometry.
- **Type label:** `paper_only`

### 4. Dual-beam spectral measurement improves accuracy of internal onion rot detection

- **Dataset or paper name:** Nishino, M., et al., *Postharvest Biology and
  Technology* (2019).
- **Original URL:** <https://www.sciencedirect.com/science/article/abs/pii/S0925521419302613>
- **License:** © Elsevier (paywalled); data not found publicly.
- **Relevance:** onion internal rot detection, spectral (non-acoustic).
- **Type label:** `paper_only`

### 5. Novel non-destructive quality assessment techniques of onion (review)

- **Dataset or paper name:** Islam, M.N., et al. (2018), *PMC6045999*.
- **Original URL:** <https://pmc.ncbi.nlm.nih.gov/articles/PMC6045999/>
- **License:** open access (PMC).
- **Relevance:** review of non-destructive onion quality methods; context for
  choosing vibrometry/acoustics research directions.
- **Type label:** `paper_only`

## Not redistributed

| Source | Reason | How to obtain |
|---|---|---|
| Coconut acoustic dataset (Mendeley `hxh8kd3snj`) | CC BY-NC-ND 4.0 — NoDerivatives forbids repacked redistribution; single 278 MB file exceeds GitHub's 100 MiB limit | Run `python tools/download_external_acoustic_data.py --item coconut --dest <local folder>` which downloads it directly from Mendeley into a **local, non-committed** folder, then verify SHA-256 `629fbc02a8ffac1a40222a2c6a536a1e4a51e812fe9defaaed93417e6c151971` |
| Landahl et al. 2022 (onion LDV) | No public dataset exists — the raw LDV vibration files were never published; the **paper itself** is CC BY 4.0 OA and may be downloaded/redistributed with attribution | Fetch the PDF in a browser from the DOI or the Cranfield bitstream link (see entry 1); cite DOI `10.1016/j.biosystemseng.2022.07.004` and Corrigendum `10.1016/j.biosystemseng.2022.10.012` |
| All other `paper_only` entries | Papers, not datasets | Follow the URLs above |

## Explicit honesty statement

No public repository of onion acoustic/impact/vibration recordings with
internal-defect labels was found during this search (2026-09-18). Until real
onion recordings are collected under `collection_protocol.md` and placed in
`raw/` with cut-open ground truth, **no acoustic model in this repository may
be described as an onion internal-defect detector**.
