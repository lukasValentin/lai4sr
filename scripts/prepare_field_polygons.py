"""
Clip field parcel polygons provided by the federal
office of agriculture (BLW) to the extent of the
image tiles and save them as geopackage files.
"""

import geopandas as gpd

from eodal.core.raster import RasterCollection
from pathlib import Path


def get_bbox(fpath: Path) -> gpd.GeoDataFrame:
    """
    Get the bounding box of a raster file.

    Parameters
    ----------
    fpath : Path
        Path to the raster file.
    return : gpd.GeoDataFrame
        GeoDataFrame with the bounding box as geometry.
    """
    rc = RasterCollection.from_multi_band_raster(fpath)
    epsg = rc[rc.band_names[0]].geo_info.epsg
    bounds = rc[rc.band_names[0]].bounds
    return gpd.GeoDataFrame(geometry=[bounds], crs=f'EPSG:{epsg}')


def main(sat_data_dir: Path, fpath_parcels: Path, year: int) -> None:
    """
    Clip field parcel polygons to the extent of the
    image tiles and save them as geopackage files.

    Parameters
    ----------
    sat_data_dir : Path
        Path to the directory with the satellite data.
    fpath_parcels : Path
        Path to the field parcel polygons.
    """
    # read the parcel polygons
    gdf = gpd.read_file(fpath_parcels)
    epsg = gdf.crs.to_epsg()

    # loop over directories in sat_data_dir
    for sat_dir in sat_data_dir.iterdir():
        sat_dir_year = sat_dir / str(year)
        # output directory for clipped parcel polygons
        output_dir_parcels = sat_dir_year.joinpath('parcels')
        output_dir_parcels.mkdir(parents=True, exist_ok=True)
        # loop over months
        for month_dir in sat_dir_year.iterdir():
            # loop over scenes
            for fpath_scene in month_dir.joinpath('data').glob('*.tif'):
                # get the bounding box of the scenes
                bbox = get_bbox(fpath_scene)
                bbox = bbox.to_crs(epsg=epsg)
                # clip the parcel polygons to the extent of the scene
                gdf_clip = gpd.clip(gdf, bbox)
                if gdf_clip.empty:
                    continue
                # save the parcel polygons as geopackage
                fpath_out = output_dir_parcels.joinpath(
                    f'{fpath_scene.stem}.gpkg')
                gdf_clip.to_file(fpath_out, driver='GPKG')

                print(f'Clipped parcel polygons for {fpath_scene.stem}')


if __name__ == '__main__':

    # Path to the field parcel polygons downloaded from
    # geodienste.ch for the year 2022
    year = 2022
    fpath_parcels = Path('data/lwb_nutzungsflaechen_lv95.gpkg')

    sat_data_dir = Path('data')

    main(sat_data_dir, fpath_parcels, year)
