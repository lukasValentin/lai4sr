"""
Run PROSAIL forward simulations for the PlanetScope dataset
using the `rtm_inv` subpackage using the parameters suggested
by Graf et al. (2023, under review).
"""

from eodal.config import get_settings
from pathlib import Path

from rtm_inv.core.config import RTMConfig
from rtm_inv.core.lookup_table import generate_lut


def run_prosail_sentinel2(path: Path):
    """
    Run PROSAIL forward simulations for each scene in
    the PlanetScope dataset

    Parameters
    ----------
    path : Path
        Path to the PlanetScope dataset
    """
    # loop over the folders. Jump into a folder if it starts
    # with two digits followed by an underscore and three letters
    for folder in path.iterdir():
        if folder.name[:2].isdigit() and folder.name[2] == '_':
            # loop over the scenes
            metadata_dir = folder / 'metadata'
            # directory for saving the LUTs to
            lut_dir = folder / 'lut'
            lut_dir.mkdir(exist_ok=True)
            for scene in metadata_dir.glob('*.xml'):
                # file name of the LUT
                lut_file = lut_dir / (scene.stem + '.pkl')
                if lut_file.exists():
                    continue
                # read the metadata
                metadata = metadata_dir / (scene.stem + '.xml')


if __name__ == '__main__':

    year = 2022
    # path to the PlanetScope dataset
    path = Path('data/sentinel2') / str(year)

    run_prosail_sentinel2(path)
