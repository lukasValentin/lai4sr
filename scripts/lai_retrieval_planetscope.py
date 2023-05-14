"""
LAI retrieval for PlanetScope data and simulated
PlanetScope data from the PROSAIL model.

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

import matplotlib.pyplot as plt
import pandas as pd

from eodal.config import get_settings
from eodal.core.band import Band
from eodal.core.raster import RasterCollection
from pathlib import Path
from typing import Optional

from rtm_inv.core.inversion import inv_img, retrieve_traits


# Bands to use for the LAI retrieval
# all eight bands of PlanetScope
ps_8bands = {
    'B1': 'coastal_blue',
    'B2': 'blue',
    'B3': 'green_i',
    'B4': 'green',
    'B5': 'yellow',
    'B6': 'red',
    'B7': 'red_edge',
    'B8': 'nir'}
# 4 bands compatabile with Sentinel-2 10 m bands
ps_4bands = {
    'B2': 'blue',
    'B4': 'green',
    'B6': 'red',
    'B8': 'nir'}
logger = get_settings().logger


def lai_retrieval_planetscope(
        path: Path,
        four_or_eight_bands: Optional[str] = 'four') -> None:
    """
    Run the LAI retrieval for PlanetScope data.

    Retrieval is either done for all 8 bands and for those
    4 bands that are compatible with Sentinel-2 10 m bands.

    Parameters
    ----------
    path : Path
        Path to the PlanetScope reflectance data
        and lookup-tables with PROSAIL simulations
    four_or_eight_bands : Optional[str]
        Either 'four' or 'eight' to indicate whether
        the retrieval should be done for 4 or 8 bands.
        Default is 'four'.
    """
    # check the input
    if four_or_eight_bands not in ['four', 'eight']:
        raise ValueError(
            f'four_or_eight_bands must be either "four" or "eight", '
            f'but is {four_or_eight_bands}')

    # determine the lai settings
    if four_or_eight_bands == 'four':
        ps_bands = ps_4bands
        lai_file_prefix = 'lai_4bands'
    else:
        ps_bands = ps_8bands
        lai_file_prefix = 'lai_8bands'

    # loop over the folders. Jump into a folder if it starts
    # with two digits followed by an underscore and three letters
    for folder in path.iterdir():
        if folder.name[:2].isdigit() and folder.name[2] == '_':
            # loop over the scenes
            data_dir = folder / 'data'
            # directory with LUTs
            lut_dir = folder / 'lut'
            # directory for storing LAI results
            lai_dir = folder / 'lai'
            lai_dir.mkdir(exist_ok=True)

            # loop over the scenes
            for scene in data_dir.glob('*.tif'):

                # skip if the scene is already processed
                fpath_lai = lai_dir / \
                    (scene.stem + f'_{lai_file_prefix}.tif')
                if fpath_lai.exists():
                    logger.info(f'Skipping {scene.name}')
                    continue

                # find the corresponding LUT
                lut_file = lut_dir / (scene.stem + '.pkl')
                # raise a warning if the LUT is not found
                if not lut_file.exists():
                    logger.warning(
                        f'No LUT found for {folder.name}: {scene.name}')
                    errored_scenes_dir = lai_dir / 'errored_scenes'
                    errored_scenes_dir.mkdir(exist_ok=True)
                    with open(
                        errored_scenes_dir /
                            'errored_scenes.txt', 'a') as f:
                        f.write(f'{scene.name}\n')
                    continue

                lut = pd.read_pickle(lut_file)
                # get the simulated reflectance data
                sim_refl = lut[list(ps_bands.keys())].values
                # read the observed reflectance data
                rc = RasterCollection.from_multi_band_raster(scene)
                obs_refl = rc.get_values(
                    band_selection=list(ps_bands.values())).astype(float)
                obs_refl *= 0.0001  # convert to reflectance [0, 1]
                # the actual inversion
                mask = obs_refl[0, :, :] == 0.
                lut_idxs, cost_function_values = inv_img(
                    lut=sim_refl,
                    img=obs_refl,
                    cost_function='rmse',
                    n_solutions=5000,
                    mask=mask
                )
                trait_img, _, _ = retrieve_traits(
                    lut=lut,
                    lut_idxs=lut_idxs,
                    traits=['lai'],
                    cost_function_values=cost_function_values,
                    measure='median'
                )

                # save lowest, median and highest cost function value
                highest_cost_function_vals = cost_function_values[-1, :, :]
                lowest_cost_function_vals = cost_function_values[0, :, :]

                # save the results
                trait_collection = RasterCollection()
                trait_collection.add_band(
                    Band,
                    geo_info=rc[rc.band_names[0]].geo_info,
                    band_name='lai',
                    values=trait_img[0, :, :]
                )
                trait_collection.add_band(
                    Band,
                    geo_info=rc[rc.band_names[0]].geo_info,
                    band_name='lowest_cost_function_value',
                    values=lowest_cost_function_vals
                )
                trait_collection.add_band(
                    Band,
                    geo_info=rc[rc.band_names[0]].geo_info,
                    band_name='highest_cost_function_value',
                    values=highest_cost_function_vals
                )
                # save as GeoTiff
                trait_collection.to_rasterio(fpath_lai)

                # save a Quicklook png
                f, ax = plt.subplots(1, 1, figsize=(10, 10))
                trait_collection['lai'].plot(
                    colormap='viridis',
                    colorbar_label=r'LAI [m$^2$ m$^{-2}$]',
                    vmin=0.,
                    vmax=8.,
                    ax=ax,
                    fontsize=18
                )
                ax.set_title('')
                fpath_lai_plot = lai_dir / \
                    (scene.stem + f'_{lai_file_prefix}.png')
                f.savefig(fpath_lai_plot, dpi=300)
                plt.close(f)

                logger.info(
                    f'Finished LAI retrieval for {folder.name}: {scene.name}')


if __name__ == '__main__':

    year = 2022
    # Set the path to the data
    path = Path('data/planetscope') / str(year)

    # by default, this use the 4 bands that are compatible with
    # Sentinel-2 10 m bands
    lai_retrieval_planetscope(path)
