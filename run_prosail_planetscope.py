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

import shutil

from eodal.config import get_settings
from pathlib import Path
from typing import Any, Dict
from xml.dom import minidom

from rtm_inv.core.config import RTMConfig
from rtm_inv.core.lookup_table import generate_lut


# metadata entries to be extracted from the xml file
eop_angle_mapping = {
    'ps:spaceCraftViewAngle': 'viewing_zenith_angle',
    'ps:azimuthAngle': 'relative_azimuth_angle',
    'opt:illuminationElevationAngle': 'sun_elevation'
}

# configuration of the PROSAIL forward simulations
platform = 'PlanetSuperDove'
# set up the RTM configuration
rtm_config = RTMConfig(
    traits=['lai'],
    lut_params=Path('prosail_parameters.csv'),
    rtm='prosail')

# set up the logger
logger = get_settings().logger


def parse_metadata_xml(in_file: Path) -> Dict[str, Any]:
    """
    Parses the metadata file (*.xml) delivered with the Planet-Scope
    mapper to extract the EPSG code of the scene and the orbit directions

    Parameters
    ----------
    in_file : Path
        Path to the metadata file
    return : Dict[str, Any]
        Dictionary containing the viewing and illimination angles
    """
    # parse the xml file into a minidom object
    xmldoc = minidom.parse(str(in_file))
    # get the acquisition parameters
    eop_params = xmldoc.getElementsByTagName(
        "eop:acquisitionParameters")[0]
    ps_params = eop_params.getElementsByTagName(
        "ps:Acquisition")[0]
    # get the angles
    angles = {}
    for eop_angle in eop_angle_mapping.items():
        angles[eop_angle[1]] = float(
            ps_params.getElementsByTagName(
                eop_angle[0])[0].firstChild.nodeValue)
    return angles


def run_prosail_planetscope(path: Path):
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
                try:
                    angles = parse_metadata_xml(metadata)
                except Exception as e:
                    logger.error(f'Could not parse {metadata}: {e}')
                    errored_xml_dir = metadata_dir / 'errored_xml'
                    errored_xml_dir.mkdir(exist_ok=True)
                    shutil.move(metadata, errored_xml_dir)
                    continue
                angles['solar_zenith_angle'] = 90 - angles['sun_elevation']
                del angles['sun_elevation']
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
    path = Path('data/planetscope') / str(year)

    run_prosail_planetscope(path)
