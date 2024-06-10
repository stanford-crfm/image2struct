# Image2Struct
[Paper](TODO) | [Website](https://crfm.stanford.edu/helm/image2structure/latest/) | Datasets ([Webpages](https://huggingface.co/datasets/stanford-crfm/i2s-webpage), [Latex](https://huggingface.co/datasets/stanford-crfm/i2s-latex), [Music sheets](https://huggingface.co/datasets/stanford-crfm/i2s-musicsheet)) | [Leaderboard](https://crfm.stanford.edu/helm/image2structure/latest/#/leaderboard) | [HELM repo](https://github.com/stanford-crfm/helm)

Welcome, the `image2struct` Python package contains code usied in the **Image2Struct: A Benchmark for Evaluating Vision-Language Models in Extracting Structured Information from Images** paper. This repo includes the following features:
* Data collection: scrapers, filters, compilers, and uploaders for the different data types (Latex, Webpages, MusicSheets) from public sources (ArXiV, GitHub, IMSLP, ...)
* Dataset upload: upload the datasets to the Hugging Face Datasets Hub
* Wild data collection: collection of screenshots from webpages specified by a determined list of URLs and formatting of equations screenshots of your choice.

This repo **does not** contain:
* The evaluation code: the evaluation code is available in the [HELM repo](https://github.com/stanford-crfm/helm).

## Installation
To install the package, you can use `pip` and `conda`:

    conda create -n image2struct python=3.9.18 -y
    conda activate image2struct
    pip install -e ".[all]"

Some formats require additional dependencies. To install all dependencies, use:

    sudo ./install-dev.sh

Finally, create a `.env` file by copying the `.env.example` file and filling in the required values.


## Usage

### Data collection

You can run `image2structure-collect` to collect data from different sources. For example, to collect data from GitHub Pages:

    image2structure-collect --num_instances 300 --num_instances_at_once 50 --max_instances_per_date 40 --date_from 2024-01-01 --date_to 2024-02-20 --timeout 30 --destination_path data webpage --language css --port 4000 --max_size_kb 100

The general arguments are:
* `--num_instances`: the number of instances to collect
* `--num_instances_at_once`: the number of instances to collect at once. This means that when the scraper is called, it won't ask the API used (here GitHub Developer API) for more than `num_instances_at_once` instances. This is useful to avoid hitting the rate limit.
* `--max_instances_per_date`: the maximum number of instances to collect for a single date. This is useful to avoid collecting too many instances for a single date.
* `--date_from`: the starting date to collect instances from.
* `--date_to`: the ending date to collect instances from.
* `--timeout`: the timeout in seconds for each instance collection.
* `--destination_path`: the path to save the collected data to.

Then you can add specific arguments for the data type you want to collect. To do so simply add the data type, here `webpage`, followed by the data-specific arguments. You can find the data-specific arguments in the `src/image2struct/run_specs.py` file.

The script will save the collected data to the specified destination path under this format:

    output_path
    ├── subcategory1
    │   ├── assets
    │   ├── images
    │   |   ├── uuid1.png
    │   |   ├── uuid2.png
    │   |   └── ...
    │   ├── metadata
    │   |   ├── uuid1.json
    │   |   ├── uuid2.json
    │   |   └── ...
    │   ├── structures # Depends on the data type
    │   |   ├── uuid1.{tex,tar.gz,...}
    │   |   ├── uuid2.{tex,tar.gz,...}
    │   |   └── ...
    │   ├── (text) # Depends on the data type
    │   |   ├── uuid1.txt
    │   |   ├── uuid2.txt
    │   |   └── ...
    ├── subcategory2
    └── ...
        

### Upload datasets

Once you have collected some datasets, you can upload them to the Hugging Face Datasets Hub. For example, to upload the latex dataset:

    image2structure-upload --data-path data/latex --dataset-name stanford-crfm/i2s-latex --max-instances 50

This will upload the dataset to the Hugging Face Datasets Hub under the `stanford-crfm/i2s-latex` dataset name. The `max-instances` argument specifies the maximum number of instances to upload. The `--data-path` argument specifies the path to the dataset files. These files should respect the format outputed by the collection scripts.


### Wild data collection

There are two scripts to build the wild datasets: `src/image2struct/wildwild/wild_latex.py` and `src/image2struct/wildwild/wild_webpage.py`. You can simply run them to format the data (you will need to collect screenshots of equations manually for the `wild_latex` script while the `wild_webpage` will take screenshots of websites by itself):

    python src/image2struct/wild/wild_webpage.py
    python src/image2struct/wild/wild_latex.py

You can then upload the datasets to the Hugging Face Datasets Hub as explained above.

## Contributing
To contribute to this project, first install the development dependencies:

    pip install -e ".[dev]"

Then, install the dependencies and git hook scripts:

    ./pre-commit.sh && pre-commit install

To run unit tests:

    python -m pytest