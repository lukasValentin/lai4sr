"""
Compare LAI results from Planet-Scope with 4 and 8 bands
by creating scatter plots of the LAI values.
"""

import numpy as np
import mpl_scatter_density  # noqa: F401
import matplotlib.pyplot as plt

from eodal.core.raster import RasterCollection
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

plt.style.use('bmh')


# "Viridis-like" colormap with white background
white_viridis = LinearSegmentedColormap.from_list('white_viridis', [
    (0, '#ffffff'),
    (1e-20, '#440053'),
    (0.2, '#404388'),
    (0.4, '#2a788e'),
    (0.6, '#21a784'),
    (0.8, '#78d151'),
    (1, '#fde624'),
], N=256)


def lai_scatter(
        fpath_4_bands: Path,
        fpath_8_bands: Path,
        output_dir: Path) -> None:
    """
    Create scatter plots of LAI values from Planet-Scope
    with 4 and 8 bands.

    Parameters
    ----------
    fpath_4_bands : Path
        Path to the LAI values from Planet-Scope with 4 bands
    fpath_8_bands : Path
        Path to the LAI values from Planet-Scope with 8 bands
    output_dir : Path
        Path to the output directory
    """
    # read the LAI values
    lai_4bands = RasterCollection.from_multi_band_raster(
        fpath_4_bands)['lai'].values
    lai_8bands = RasterCollection.from_multi_band_raster(
        fpath_8_bands)['lai'].values

    # calculate R2
    lai_4bands_nonan = lai_4bands[~np.isnan(lai_4bands)]
    lai_8bands_nonan = lai_8bands[~np.isnan(lai_8bands)]
    r2 = np.corrcoef(
        lai_4bands_nonan, lai_8bands_nonan)[0, 1]**2

    # make a scatter plot and color the points by density
    fig = plt.Figure(figsize=(6, 6))
    ax = fig.add_subplot(1, 1, 1, projection='scatter_density')
    density = ax.scatter_density(
        lai_4bands_nonan,
        lai_8bands_nonan,
        cmap=white_viridis)
    fig.colorbar(density, label='Density')
    ax.set_xlabel(r'Planet SuperDove LAI 4 bands [m$^2$ m$^{-2}$]')
    ax.set_ylabel(r'Planet SuperDove LAI 8 bands [m$^2$ m$^{-2}$]')
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    ax.set_aspect('equal')
    ax.set_title(r'$R^2$ = ' + str(np.round(r2, 2)) +
                 f'; N = {lai_4bands.size}')

    # save the figure
    scene = fpath_4_bands.stem.split('_')[0]
    fpath = output_dir / f'{scene}_lai_4_vs_8_bands.png'
    fig.savefig(fpath, dpi=300)
    plt.close(fig)


def lai_difference_maps(
        fpath_4_bands: Path,
        fpath_8_bands: Path,
        output_dir: Path) -> None:
    """
    Create difference maps of LAI values from Planet-Scope
    with 4 and 8 bands.

    Parameters
    ----------
    fpath_4_bands : Path
        Path to the LAI values from Planet-Scope with 4 bands
    fpath_8_bands : Path
        Path to the LAI values from Planet-Scope with 8 bands
    output_dir : Path
        Path to the output directory
    """

    # read the LAI values
    lai_4bands = RasterCollection.from_multi_band_raster(
        fpath_4_bands)['lai']
    lai_8bands = RasterCollection.from_multi_band_raster(
        fpath_8_bands)['lai']

    # calculate the difference (8 minus 4 band LAI)
    lai_diff = lai_4bands - lai_8bands

    # plot the differences with a diverging color map
    fig, ax = plt.subplots(figsize=(5, 5))
    lai_diff.plot(
        colormap='coolwarm',
        colorbar_label=r'Difference in LAI [$m^2$ $m^{-2}$]',
        ax=ax
    )
    ax.set_title('PlanetScope 4-band LAI minus 8-band LAI')

    # save the figure
    scene = fpath_4_bands.stem.split('_')[0]
    fname = output_dir / f'{scene}_lai_4_minus_8_bands.png'
    fig.savefig(fname, dpi=300, bbox_inches='tight')
    plt.close(fig)

    # histogram of differences
    fig, ax = plt.subplots(figsize=(5,5))
    lai_diff.hist(bins=100, ax=ax)
    ax.set_xlabel(r'Difference in LAI [$m^2$ $m^{-2}$]')
    fname = output_dir / f'{scene}_lai_4_minus_8_bands_hist.png'
    fig.savefig(fname, dpi=300, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':

    fpath_4bands = Path(
        'data/planetscope/2022/09_sep/lai/0128_lai_4bands.tif')
    fpath_8bands = Path(
        'data/planetscope/2022/09_sep/lai/0128_lai_8bands.tif')

    output_dir = Path('analysis/planetscope_4_vs_8_bands')
    output_dir.mkdir(exist_ok=True, parents=True)

    lai_difference_maps(fpath_4bands, fpath_8bands, output_dir)

    lai_scatter(fpath_4bands, fpath_8bands, output_dir)
