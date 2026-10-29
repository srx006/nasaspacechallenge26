# ISTMOSAR data contract (JP-06) — `contracts/`

Contract version **`1.0.0-rc.1`** (release candidate). Specification: [`docs/JP-06-API-Data-Contract.md`](../docs/JP-06-API-Data-Contract.md). Review findings: [`docs/JP-06-Review-Report.md`](../docs/JP-06-Review-Report.md).

This folder holds **design artifacts only**: JSON Schemas, example payloads and their tests. There is no FastAPI app, no satellite processing and no computed satellite result here. A passing validation proves the JSON is well-formed and internally consistent. It does **not** prove that any observation, pair, raster or statistic is scientifically correct or approved.

## Layout

```text
contracts/
  schemas/                  JSON Schema Draft 2020-12 (normative)
    common.schema.json        shared definitions: ids, UTC timestamps, lon/lat, enums, review record
    study-area.schema.json    A. study area
    scene.schema.json         B. NISAR GCOV scene (catalog facts vs HDF5-inspected facts)
    layer.schema.json         C. geographic layer (scientific raster vs browser delivery)
    analysis.schema.json      D. pairwise analysis (decision / lifecycle / approval)
    statistics.schema.json    E. statistics (null = not computed, never 0)
    provenance.schema.json    F. reproducibility record
    error.schema.json         G. API error body
    api-responses.schema.json health + list envelopes {contract_version, items, page}
  examples/                 fixtures, each registered in the manifest
  fixtures-manifest.json    fixture -> schema + category, and 50 mutation (negative/positive) tests
  requirements.txt          validator dependency
```

## Run the validator (from the repository root)

```text
pip install -r contracts/requirements.txt
python validate_contracts.py              # exit 0 = pass, 1 = failures, 2 = environment error
python validate_contracts.py -v           # list every passing check
python validate_contracts.py --verify-catalog   # ONLINE, optional: compare verified scenes with live NASA CMR
```

Works on Windows, macOS and Linux with Python 3.10+. The `[format-nongpl]` extra in `requirements.txt` is required: without it the `date-time` and `uri` format keywords are silently ignored, so the validator refuses to run.

## Fixture categories

| Category | Meaning | File naming |
|---|---|---|
| `VERIFIED_METADATA` | copied from an independently checked official NASA record | `*.catalog.json`, `analysis-*-NO-GO.json` |
| `PROPOSED_STRUCTURE` | design example of the intended API shape | `api-*.json`, `error-*.json`, `study-area-*.json` |
| `SIMULATED_DATA` | artificial, never satellite data | **must** contain `.simulated.`; URLs use `example.invalid` |
| `UNAVAILABLE` | a result that has not been generated | statistics / layers in blocked analyses |

## Add or change something

1. Edit the schema first, then the fixtures. Real facts must come from the official CMR record, never from memory.
2. Register every new file in `fixtures-manifest.json` (`file`, `schema`, `category`, `description`). Unregistered files fail validation.
3. Add a mutation case for every new rule. A case names a base fixture and a JSON patch (`add`/`replace`/`remove`) and states the expected outcome: `invalid` at stage `schema` or `business`, or `valid`.
4. Run the validator. Bump the contract version (schemas are addressed by `$id`; the version appears in `api-health.json` and the manifest) and record the change in `docs/JP-06-API-Data-Contract.md`.

Save files as UTF-8 **without BOM** (some Windows tools add one). Never put Earthdata tokens, passwords, local file paths or HDF5 files in this folder.
