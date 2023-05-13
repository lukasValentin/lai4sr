"""
LAI retrieval for PlanetScope data and simulated
PlanetScope data from the PROSAIL model.
"""

import matplotlib.pyplot as plt
import pandas as pd

from eodal.config import get_settings
from eodal.core.band import Band
from eodal.core.raster import RasterCollection
from pathlib import Path

from rtm_inv.core.inversion import inv_img, retrieve_traits

# Bands to use for the LAI retrieval
ps_bands = [
    'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8'
]
logger = get_settings().logger


def lai_retrieval_planetscope(path: Path) -> None:
    """
    Run the LAI retrieval for PlanetScope data.

    Parameters
    ----------
    path : Path
        Path to the PlanetScope reflectance data
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

                # skip if the scene is already processed
                fpath_lai = lai_dir / (scene.stem + '_lai.tif')
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
                sim_refl = lut[ps_bands].values
                # read the observed reflectance data
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

    year = 2022
    # Set the path to the data
    path = Path('data/planetscope') / str(year)

    lai_retrieval_planetscope(path)
