"""
Download satellite data prepared by Julian Neff,
and unzip it into the data folder.
"""

import requests
import zipfile
from pathlib import Path


def download_data(url: str, filename: str) -> None:
    """
    Download satellite data from Julian Neff's github repo.

    Parameters
    ----------
    url : str
        URL to download data from.
    filename : str
        Name of file to save data to.
    """
    # download the data using the requests library,
    # save it to a zip with filename, and unzip it
    r = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(r.content)
    data_dir = Path.cwd().joinpath('data')
    data_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(data_dir)


if __name__ == '__main__':

    # download the Planet-Scope data
    url = 'https://polybox.ethz.ch/index.php/s/1n5zC3CZGd4ECBQ/download'
    filename = 'planetscope.zip'

    download_data(url, filename)
