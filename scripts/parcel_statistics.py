"""
Calculate the coefficient of variation, entropy and other
statistical measures for each parcel using EOdal.

@date: 2023-05-18
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

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import warnings

from eodal.core.raster import RasterCollection
from functools import wraps
from pathlib import Path

warnings.filterwarnings('ignore')
common_crs = 'EPSG:2056'


def masked_array_to_ndarray(func):
    """
    Decorator to convert a masked array to a numpy array
    and checks for nan values.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        x = args[0]
        if isinstance(x, np.ma.MaskedArray):
            x = x.filled(np.nan)
            if np.isnan(x).all():
                return np.nan
        return func(x, **kwargs)
    return wrapper


@masked_array_to_ndarray
def coefficient_of_variation(x: np.ma.MaskedArray) -> float:
    """
    Calculate the coefficient of variation for a raster array.

    :param x:
        array with raster values
    :returns:
        median absolute deviation value
    """
    return np.nanstd(x, axis=None) / np.nanmean(x)


@masked_array_to_ndarray
def entropy(x: np.ma.MaskedArray) -> float:
    """
    Calculate the entropy for a raster array.

    :param x:
        array with raster values
    :returns:
        entropy value
    """
    p = np.unique(x, return_counts=True)[1] / x.size
    return -np.sum(p * np.log(p))


def compute_parcel_statistics(
        data_dir: Path,
        year: int
) -> None:
    """
    Calculate the coefficient of variation, entropy and other
    statistical measures for each parcel

    Parameters
    ----------
    data_dir : Path
        Path to the directory with the satellite data.
    year : int
        Year of the satellite data.
    """
    # loop over directories in sat_data_dir
    for sat_dir in data_dir.iterdir():
        sat_dir_year = sat_dir / str(year)
        if not sat_dir_year.exists():
            continue
        # directory with clipped parcel polygons
        parcels_dir = sat_dir_year.joinpath('parcels')

        # loop over months
        for month_dir in sat_dir_year.iterdir():
            # directory with LAI data
            lai_dir = month_dir.joinpath('lai')
            # loop over lai files
            for fpath_lai in lai_dir.glob('*.tif'):
                # get the parcel polygons
                scene = fpath_lai.stem.split('_lai')[0]
                fpath_parcels = parcels_dir.joinpath(
                    scene + '.gpkg')
                if not fpath_parcels.exists():
                    continue
                gdf = gpd.read_file(fpath_parcels)

                # read the LAI data
                lai = RasterCollection.from_multi_band_raster(
                    fpath_lai)['lai']
                gdf.to_crs(lai.crs, inplace=True)

                # calculate the statistics
                try:
                    lai_stats = lai.reduce(
                        by=gdf,
                        method=['median', 'count', 'mean', 'min', 'max',
                                'percentile_10', 'percentile_90', 'std',
                                entropy, coefficient_of_variation])
                    # convert to GeoDataFrame
                    gdf_stats = gpd.GeoDataFrame(
                        lai_stats, geometry='geometry', crs=lai.crs)
                    # drop the CRS column
                    gdf_stats.drop(columns=['crs'], inplace=True)

                    # save the statistics
                    fpath_stats = lai_dir.joinpath(
                        fpath_lai.stem + '_parcel_stats.gpkg')
                    gdf_stats.to_file(fpath_stats, driver='GPKG')
                except Exception as e:
                    print(e)
                    continue


def get_parcel_statistics(
        data_dir: Path,
        year: int
) -> None:
    """
    Collect the parcel statistics and save them into
    a single file per plaform (PlanetScope and Sentinel2).

    Parameters
    ----------
    data_dir : Path
        Path to the directory with the satellite data.
    year : int
        Year of the satellite data.
    """
    # loop over directories in sat_data_dir
    for sat_dir in data_dir.iterdir():
        platform = sat_dir.name
        sat_dir_year = sat_dir / str(year)
        if not sat_dir_year.exists():
            continue
        # loop over months
        platform_stats_list = []
        for month_dir in sat_dir_year.iterdir():
            # loop over statistics files
            for fpath_stats in month_dir.joinpath('lai').glob('*_parcel_stats.gpkg'):
                # configuration of the LAI retrieval
                config = fpath_stats.stem.split('_')[2]
                # read the statistics
                gdf_stats = gpd.read_file(fpath_stats)
                # drop NaN values, i.e., where count is 0
                gdf_stats = gdf_stats[gdf_stats['count'] > 0].copy()
                gdf_stats['scene'] = fpath_stats.stem.split('_')[0]
                gdf_stats['platform'] = platform
                gdf_stats['month'] = month_dir.name
                gdf_stats['config'] = config
                gdf_stats.to_crs(common_crs, inplace=True)
                platform_stats_list.append(gdf_stats)

        # concatenate the statistics
        platform_stats = gpd.GeoDataFrame(
            pd.concat(platform_stats_list, ignore_index=True),
            geometry='geometry', crs=gdf_stats.crs)
        # save as GeoPackage
        fpath_stats = sat_dir_year.joinpath(
            'parcel_statistics.gpkg')
        platform_stats.to_file(fpath_stats, driver='GPKG')

        print(f'Platform: {platform} ({year}) --> done')


def compare_planetscope_lai(
        fpath_planetscope: Path,
        out_dir: Path
) -> None:
    """
    Compare PlanetScope 4 and 8 band LAI retrievals.

    Parameters
    ----------
    fpath_planetscope : Path
        Path to the PlanetScope LAI retrieval.
    out_dir : Path
        Path to the output directory.
    """
    # read the file
    gdf = gpd.read_file(fpath_planetscope)
    # plot the coefficient of variation and the entropy
    # by config using seaborn
    sns.set_theme(style="whitegrid")
    sns.set_context("paper")
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    sns.boxplot(x='config', y='coefficient_of_variation',
                data=gdf, ax=ax[0], order=['4bands', '8bands'])
    sns.boxplot(x='config', y='entropy',
                data=gdf, ax=ax[1], order=['4bands', '8bands'])
    fig.suptitle(f'PlanetScope 4 and 8 band LAI retrievals (N={gdf.shape[0]})')
    plt.tight_layout()
    fig.savefig(out_dir.joinpath('boxplots.png'), dpi=300)
    plt.close(fig)

    # loop over the months and do the same plots per month
    for month in gdf['month'].unique():
        fig, ax = plt.subplots(1, 2, figsize=(10, 5))
        sns.boxplot(x='config', y='coefficient_of_variation',
                    data=gdf[gdf['month'] == month], ax=ax[0],
                    order=['4bands', '8bands'])
        sns.boxplot(x='config', y='entropy',
                    data=gdf[gdf['month'] == month], ax=ax[1],
                    order=['4bands', '8bands'])
        fig.suptitle(
            f'PlanetScope 4 and 8 band LAI retrievals ({month})\n' +
            f'N = {gdf[gdf["month"] == month].shape[0]} parcels')
        plt.tight_layout()
        fig.savefig(out_dir.joinpath(f'boxplots_{month}.png'), dpi=300)
        plt.close(fig)


def compare_sentinel2_lai(
        fpath_sentinel2: Path,
        out_dir: Path
) -> None:
    """
    Compare Sentinel2 10 and 20 m LAI retrievals.

    Parameters
    ----------
    fpath_sentinel2 : Path
        Path to the Sentinel2 LAI retrieval.
    out_dir : Path
        Path to the output directory.
    """
    # read the file
    gdf = gpd.read_file(fpath_sentinel2)
    # plot the coefficient of variation and the entropy
    # by config using seaborn
    sns.set_theme(style="whitegrid")
    sns.set_context("paper")
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    sns.boxplot(x='config', y='coefficient_of_variation',
                data=gdf, ax=ax[0], order=['10m', '20m'])
    sns.boxplot(x='config', y='entropy',
                data=gdf, ax=ax[1], order=['10m', '20m'])
    fig.suptitle(f'Sentinel2 10 and 20 m LAI retrievals (N={gdf.shape[0]})')
    plt.tight_layout()
    fig.savefig(out_dir.joinpath('boxplots.png'), dpi=300)
    plt.close(fig)

    # loop over the months and do the same plots per month
    for month in gdf['month'].unique():
        fig, ax = plt.subplots(1, 2, figsize=(10, 5))
        sns.boxplot(x='config', y='coefficient_of_variation',
                    data=gdf[gdf['month'] == month], ax=ax[0],
                    order=['10m', '20m'])
        sns.boxplot(x='config', y='entropy',
                    data=gdf[gdf['month'] == month], ax=ax[1],
                    order=['10m', '20m'])
        fig.suptitle(
            f'Sentinel2 10 and 20 m LAI retrievals ({month})\n' +
            f'N = {gdf[gdf["month"] == month].shape[0]} parcels')
        plt.tight_layout()
        fig.savefig(out_dir.joinpath(f'boxplots_{month}.png'), dpi=300)
        plt.close(fig)


if __name__ == '__main__':

    year = 2022
    data_dir = Path('data')

    # compute the statistics
    # compute_parcel_statistics(data_dir, year)

    # and put them together
    # get_parcel_statistics(data_dir, year)

    # compare PlanetScope 4 and 8 band LAI retrievals
    fpath_planetscope = Path('data/planetscope/2022/parcel_statistics.gpkg')
    out_dir = Path('analysis/planetscope_4_vs_8_bands')
    compare_planetscope_lai(fpath_planetscope, out_dir)

    # compare Sentinel2 10 and 20 m LAI retrievals
    fpath_sentinel2 = Path('data/sentinel/2022/parcel_statistics.gpkg')
    out_dir = Path('analysis/sentinel2_10_vs_20_m')
    out_dir.mkdir(exist_ok=True, parents=True)
    compare_sentinel2_lai(fpath_sentinel2, out_dir)
