import datetime
from dataclasses import dataclass


@dataclass
class DatasetProperties:
    """
    Dataclass for dataset properties.
    """

    # Path to the dataset
    path: str

    # Name of the dataset
    name: str

    # Number of images in the dataset
    data_published_after: datetime.datetime
