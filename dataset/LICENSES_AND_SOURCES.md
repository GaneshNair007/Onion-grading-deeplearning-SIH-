# Licenses and Sources

Every source archive and dataset directory detected under the repository
root, with any license information that was found **bundled with the data**.
Nothing here was invented; where no license metadata exists, that is stated
explicitly.

## 1. `Onion Grading.v7i.coco-segmentation/` (+ `.zip`)

* **Contents:** 2,968 files — 2,963 `.jpg`, 3 `.json` (COCO segmentation
  annotations for `train`/`valid`/`test`), 2 Roboflow README `.txt` files.
  Size: 73,349,356 bytes (extracted) / 72,800,885 bytes (zip).
* **Included in repo parts?** Yes — extracted folder, as
  `onion-grading-coco-segmentation/`. The zip was skipped (CRC-32-verified
  bit-identical to the extracted folder).
* **Source URL** (from bundled `README.dataset.txt`):
  <https://universe.roboflow.com/edward-csxhu/onion-grading>
* **Version:** Onion Grading - v7, 2024-07-11 6:47am; exported via
  roboflow.com on July 30, 2024 (per `README.roboflow.txt`).
* **License (bundled):** CC BY 4.0 (per `README.dataset.txt`).
* Citation/DOI: none found in the bundled metadata.

## 2. `onions.v1i.coco-mmdetection/` (+ `.zip`)

* **Contents:** 786 files — 783 `.jpg`, 1 `.json` (COCO annotations for
  `train`), 2 Roboflow README `.txt` files.
  Size: 35,957,280 bytes (extracted) / 35,774,700 bytes (zip).
* **Included in repo parts?** Yes — extracted folder, as
  `onion-coco-mmdetection/`. The zip was skipped (CRC-32-verified
  bit-identical to the extracted folder).
* **Source URL** (from bundled `README.dataset.txt`):
  <https://universe.roboflow.com/onion-grading/onions-ciqkj>
* **Version:** onions - v1, 2023-01-29 2:53am; exported via roboflow.com
  on September 18, 2026 (per `README.roboflow.txt`).
* **License (bundled):** Public Domain (per `README.dataset.txt`).
* Citation/DOI: none found in the bundled metadata.

## 3. `Onion Leaves and Bulb Dataset/` (+ `.zip`)

* **Contents:** 16,300 `.jpg` files in a folder-per-class layout:
  `New Onion - Copy/1. Leaves/{1. Healthy,2. Unhealthy}/{1. Single,2. Multiple}/`
  and `New Onion - Copy/2. Bulb/{1. Healthy,2. Unhealthy}/{1. Red Onion,2. White Onion}/{1. Single,2. Multiple}/`.
  Size: 1,635,717,054 bytes (extracted) / 1,608,618,402 bytes (zip).
* **Included in repo parts?** Yes — extracted folder, as
  `onion-leaves-and-bulb/New Onion - Copy/…`.
  The zip (1.61 GB) **exceeds GitHub's 100 MiB per-file limit and is NOT
  included**; it was CRC-32-verified bit-identical to the extracted folder,
  so no content is lost. The original remains on local disk untouched.
* **Source URL:** none — no download URL, README, license, citation, or DOI
  file exists anywhere inside this dataset.
* **Collection notes:** none available locally.
* **License not detected — verify before redistribution.**

## Bundled license/README files preserved in the parts

The following original metadata files are copied verbatim into the parts and
remain the authoritative license statements:

| File (inside parts) | Group |
|---|---|
| `onion-grading-coco-segmentation/README.dataset.txt` | Roboflow Onion Grading v7 |
| `onion-grading-coco-segmentation/README.roboflow.txt` | Roboflow Onion Grading v7 |
| `onion-coco-mmdetection/README.dataset.txt` | Roboflow onions v1 |
| `onion-coco-mmdetection/README.roboflow.txt` | Roboflow onions v1 |

No other LICENSE, CITATION, DOI, or README files were detected in any
dataset directory or archive.

## Verification method used

For each source archive, the central-directory listing (names + sizes) was
compared against the extracted folder, and every entry's CRC-32 was checked
against the extracted file's content (20,054 entries, 0 mismatches). This is
the basis for treating the three `.zip` files as redundant duplicates and
excluding them from the repository.
