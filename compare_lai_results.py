"""
Compare LAI results from Planet-Scope and Sentinel-2.
This script allows to create comparison plots for the LAI
and simulated spectra.

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

from eodal.core.raster import RasterCollection
from pathlib import Path


def plot_lai_maps(lai_s2: Path, lai_ps: Path, out_dir: Path) -> None:
    """
    Plot maps of the LAI retrieved from Sentinel-2 and PlanetScope
    side by side.

    Parameters
    ----------
    lai_s2 : Path
        Path to the LAI map retrieved from Sentinel-2
    lai_ps : Path
        Path to the LAI map retrieved from PlanetScope
    out_dir : Path
        Path to the directory for storing the plots
    """
    s2 = RasterCollection.from_multi_band_raster(lai_s2)
    ps = RasterCollection.from_multi_band_raster(lai_ps)
    scene = lai_s2.stem.split('_')[0]
    spatial_res_s2 = lai_s2.stem.split('_')[2]

    # plot the LAI maps
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(10, 5),
                           sharey=True, sharex=True)
    band_name = 'lai'

    s2[band_name].plot(ax=ax[0], vmin=0, vmax=8,
                       colormap='viridis')
    ps[band_name].plot(ax=ax[1], vmin=0, vmax=8,
                       colormap='viridis')
    ax[0].set_title(f'Sentinel-2 {band_name.upper()}' +
                    f' ({spatial_res_s2})')
    ax[1].set_title(f'PlanetScope {band_name.upper()}')

    # save the plot
    fname_plot = out_dir / \
        f'{scene}_lai_s2-{spatial_res_s2}_ps.png'
    fig.savefig(fname_plot, dpi=300, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':

    # user inputs
    year = '2022'
    month = '09_sep'  # '04_apr', '05_may', or '06_jun'
    scene = '0058'   # '0000' to '0295
    spatial_res_s2 = '20m'  # 10m or 20m
    out_dir = Path('analysis/compare_lai_results')  # ignored by git
    out_dir.mkdir(exist_ok=True, parents=True)

    # set the paths to the LAI maps according to the user inputs
    # LUT maps
    lai_s2 = Path(
        f'data/sentinel/{year}/{month}/lai/{scene}_scene_' +
        f'{spatial_res_s2}_lai.tif')
    lai_ps = Path(
        f'data/planetscope/{year}/{month}/lai/{scene}_lai.tif')

    # plot the LAI values
    plot_lai_maps(lai_s2=lai_s2, lai_ps=lai_ps, out_dir=out_dir)
