import csv
import os
from main import get_asset_names_used

SUBJECTS = ["cs", "q-bio", "q-fin", "stat", "eess", "econ", "math", "physics"]
CATEGORIES = ["equation", "figure", "table", "plot", "algorithm"]
NUM_ASSETS = 10
COLUMNS = ["id", "tex_code", "category", "subject", "output"] + [
    f"asset_{i}" for i in range(NUM_ASSETS)
]


def create_csv_file():
    for category in CATEGORIES:
        with open(f"dataset_{category}.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(COLUMNS)
            id_counter = 1
            for subject in SUBJECTS:
                print(f"Category {category}")
                for i in range(
                    0, len(os.listdir(f"data/{subject}/contents/{category}s"))
                ):
                    tex_code_path = (
                        f"data/{subject}/contents/{category}s/{category}_{i}.tex"
                    )
                    image_path = f"data/{subject}/images/{category}s/{category}_{i}.png"
                    if os.path.exists(tex_code_path) and os.path.exists(image_path):
                        tex_code = open(tex_code_path).read()
                        assets = get_asset_names_used(tex_code)
                        for i in range(len(assets)):
                            assets[i] = f"assets/{subject}/{assets[i]}"
                        if (
                            len(assets) <= NUM_ASSETS
                            and len(tex_code) <= 10000
                            and (
                                len(assets) == 0
                                or category == "figure"
                                or category == "plot"
                            )
                        ):
                            row = (
                                [id_counter, tex_code_path, category, subject]
                                + [image_path]
                                + assets
                                + ["" for i in range(NUM_ASSETS - len(assets))]
                            )
                            writer.writerow(row)
                            id_counter += 1
                        elif (
                            len(assets) > 0
                            and category != "figure"
                            and category != "plot"
                        ):
                            print(
                                f"Skipping entry {id_counter} due to assets in non-figure category."
                            )
                        elif len(tex_code) > 10000:
                            print(
                                f"Skipping entry {id_counter} due to tex_code length > 10000."
                            )
                        else:
                            print(
                                f"Skipping entry {id_counter} due to more than {NUM_ASSETS} assets."
                            )
                    else:
                        print(
                            f"Skipping entry {id_counter} due to missing tex_code or image."
                        )
                    id_counter += 1


create_csv_file()
