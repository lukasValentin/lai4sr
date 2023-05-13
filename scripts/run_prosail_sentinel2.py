"""
Run PROSAIL forward simulations for the PlanetScope dataset
using the `rtm_inv` subpackage using the parameters suggested
by Graf et al. (2023, under review).

@date: 2023-05-13
@author: Lukas Valentin Graf, ETH Zurich

Copyright (C) 2023 Lukas Valentin Graf

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from eodal.config import get_settings
from eodal.metadata.sentinel2.parsing import parse_MTD_TL
from pathlib import Path

from rtm_inv.core.config import RTMConfig
from rtm_inv.core.lookup_table import generate_lut


# metadata entries to be extracted from the xml file
s2_angle_mapping = {
    'SENSOR_ZENITH_ANGLE': 'viewing_zenith_angle',
    'SENSOR_AZIMUTH_ANGLE': 'viewing_azimuth_angle',
    'SUN_AZIMUTH_ANGLE': 'solar_azimuth_angle',
    'SUN_ZENITH_ANGLE': 'solar_zenith_angle'
}
# platform mapping
s2_platform_mapping = {
    'S2A': 'Sentinel2A',
    'S2B': 'Sentinel2B'}

# set up the RTM configuration
rtm_config = RTMConfig(
    traits=['lai'],
    lut_params=Path('prosail_parameters.csv'),
    rtm='prosail')

# set up the logger
logger = get_settings().logger


def run_prosail_sentinel2(path: Path) -> None:
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
                # parse the metadata
                metadata_df = parse_MTD_TL(str(metadata))
                angles = {}
                for s2_angle in s2_angle_mapping.items():
                    angles[s2_angle[1]] = float(
                        metadata_df[s2_angle[0]])
                # check the sensor
                sensor = metadata_df['SCENE_ID'].split('_')[0]
                platform = s2_platform_mapping[sensor]
                # run the PROSAIL forward simulation
                lut = generate_lut(
                    sensor=platform,
                    lut_params=rtm_config.lut_params,
                    remove_invalid_green_peaks=True,
                    sampling_method='frs',
                    lut_size=50000,
                    **angles)
                # drop NaNs in the LUT
                lut = lut.dropna()
                # save the LUT as pickle
                lut.to_pickle(lut_file)
                logger.info(f'Processed {folder.name}: {scene.name}')


if __name__ == '__main__':

    year = 2022
    # path to the PlanetScope dataset
    path = Path('data/sentinel') / str(year)

    run_prosail_sentinel2(path)
