"""
Bootstrap minimal seed data for testing.

Creates placeholder PLZ and city files using Faker
so the pipeline can run without downloading real data.

For production datasets, replace these with real PLZ data from:
- https://www.suche-postleitzahl.org/downloads
- GENESIS-Online (destatis.de)

Usage: python seeds/bootstrap_seeds.py
"""

import csv
from pathlib import Path
from faker import Faker

fake = Faker("de_DE")
Faker.seed(42)

SEEDS_DIR = Path(__file__).parent

# Bavarian cities and PLZ (real, commonly known)
BAVARIAN_CITIES = [
    ("80331", "München"), ("90402", "Nürnberg"), ("93047", "Regensburg"),
    ("86150", "Augsburg"), ("97070", "Würzburg"), ("95444", "Bayreuth"),
    ("91052", "Erlangen"), ("92637", "Weiden i.d.OPf."), ("92249", "Vilseck"),
    ("95100", "Selb"), ("84028", "Landshut"), ("94032", "Passau"),
    ("87435", "Kempten"), ("83022", "Rosenheim"), ("85049", "Ingolstadt"),
    ("96047", "Bamberg"), ("92224", "Amberg"), ("63739", "Aschaffenburg"),
    ("91522", "Ansbach"), ("85354", "Freising"), ("82152", "Planegg"),
    ("91301", "Forchheim"), ("92318", "Neumarkt i.d.OPf."), ("93413", "Cham"),
    ("92526", "Oberviechtach"), ("95615", "Marktredwitz"),
]

# Major German cities outside Bavaria
OTHER_CITIES = [
    ("10115", "Berlin"), ("20095", "Hamburg"), ("50667", "Köln"),
    ("60311", "Frankfurt am Main"), ("70173", "Stuttgart"),
    ("40213", "Düsseldorf"), ("44135", "Dortmund"), ("45127", "Essen"),
    ("04109", "Leipzig"), ("01067", "Dresden"), ("28195", "Bremen"),
    ("30159", "Hannover"), ("68159", "Mannheim"), ("76131", "Karlsruhe"),
    ("55116", "Mainz"), ("24103", "Kiel"), ("39104", "Magdeburg"),
    ("99084", "Erfurt"), ("66111", "Saarbrücken"), ("14467", "Potsdam"),
    ("18055", "Rostock"), ("07743", "Jena"), ("09111", "Chemnitz"),
    ("33098", "Paderborn"), ("48143", "Münster"), ("79098", "Freiburg"),
]

ALL_CITIES = BAVARIAN_CITIES + OTHER_CITIES


def main():
    # Write PLZ file
    plz_path = SEEDS_DIR / "german_plz.csv"
    with open(plz_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["plz", "ort"])
        for plz, ort in ALL_CITIES:
            writer.writerow([plz, ort])
        # Add some Faker-generated entries for variety
        for _ in range(200):
            writer.writerow([fake.postcode(), fake.city()])
    print(f"Written {len(ALL_CITIES) + 200} entries to {plz_path}")

    # Write cities file
    cities_path = SEEDS_DIR / "german_staedte.csv"
    with open(cities_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ort"])
        for _, ort in ALL_CITIES:
            writer.writerow([ort])
        for _ in range(200):
            writer.writerow([fake.city()])
    print(f"Written {len(ALL_CITIES) + 200} entries to {cities_path}")

    print("Done. Replace these with real PLZ data for production datasets.")


if __name__ == "__main__":
    main()
