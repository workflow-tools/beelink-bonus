# Seed Data

Place reference data files here for weighted sampling and model fitting.

## Required files for mittelstand-b2b dataset:

- `german_plz.csv` — German postal codes (5-digit PLZ, one per line or with city column)
- `german_staedte.csv` — German city names (one per line)

## Where to get these:

**German PLZ list:**
Download from GENESIS-Online (destatis.de) or use the OpenStreetMap
Nominatim extract. A free list is available at:
https://www.suche-postleitzahl.org/downloads

**German city names:**
Extract from the PLZ list above, or from the Gemeindeverzeichnis at GENESIS-Online.

## Quick bootstrap (generates minimal test seeds):

```bash
python seeds/bootstrap_seeds.py
```
