"""
LAI retrieval for Sentinel-2 data and simulated
PlanetScope data from the PROSAIL model.

Two different setups are used:
1. Retrieval of LAI from Sentinel-2 10 m bands
2. Retrieval of LAI from Sentinel-2 20 m bands

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

from rtm_inv.core.inversion import inv_img, retrieve_traits

# Bands to use for the LAI retrieval
s2_bands_10m = ['B02', 'B03', 'B04', 'B08']
s2_bands_20m = ['B05', 'B06', 'B07', 'B8A', 'B11', 'B12']
s2_bands = {'10m': s2_bands_10m, '20m': s2_bands_20m}

logger = get_settings().logger


def lai_retrieval_sentinel2(path: Path) -> None:
    """
    Run the LAI retrieval for Sentinel2 data.
    The script produces LAI maps from the 10 and 20 m
    bands.

    Parameters
    ----------
    path : Path
        Path to the Sentinel-2 reflectance data
        and lookup-tables with PROSAIL simulations
    """
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

                # check the spatial resolution of the scene
                spatial_res_scene = scene.stem.split('_')[-1]
                if spatial_res_scene not in s2_bands.keys():
                    continue

                # skip if the scene is already processed
                fpath_lai = lai_dir / (scene.stem + '_lai.tif')
                if fpath_lai.exists():
                    logger.info(f'Skipping {scene.name}')
                    continue

                # find the corresponding LUT
                lut_file = lut_dir / (scene.stem.split('_')[0] + '_MTD_TL.pkl')
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
                sim_refl = lut[s2_bands[spatial_res_scene]].values

                # get the reflectance dataset
                rc = RasterCollection.from_multi_band_raster(scene)
                obs_refl = rc.get_values()

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
                fpath_lai_plot = lai_dir / (scene.stem + '_lai.png')
                f.savefig(fpath_lai_plot, dpi=300)
                plt.close(f)

                logger.info(
                    f'Finished LAI retrieval for {folder.name}: {scene.name}')


if __name__ == '__main__':

    # path to the Sentinel2 data
    path = Path('data/sentinel/2022')

    lai_retrieval_sentinel2(path)
