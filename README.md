# lai4sr
Generating Leaf Area Index Data For Super-Resolution

## Overview
This repository contains code to retrieve the Leaf Area Index (LAI) from Sentinel-2 and PlanetScope SuperDove optical satellite imagery by means of radiative transfer model (RTM) inversion. We use the leaf RTM PROSPECT-D together with the canopy RTM SAIL, a.k.a PROSAIL using a [FORTRAN implementation with Python interface](https://github.com/EOA-team/PyProSAIL) for maximum performance.

Inversion is performed using Lookup-tables. More details about the retrieval workflow and the RTM parameters used can be found [here](https://github.com/EOA-team/sentinel2_crop_traits).

The results are fed into a deep-learning based super-resolution model developed by @neffjulian (see [here](https://github.com/neffjulian/remote_sensing)).

## Getting started

### Satellite data
Download the PlanetScope and Sentinel-2 L2A data (image tiles of size 2 by 2 km), unzip and place them in a folder `data` in the project root.

- [Download Sentinel-2 data](https://polybox.ethz.ch/index.php/s/f3A3sP40G3MKvBJ)
- [Download PlanetScope data](https://polybox.ethz.ch/index.php/s/1n5zC3CZGd4ECBQ)

### Python requirements

All dependencies can be installed into a clean virtual environment using:

```bash
pip install -r requirements.txt
```

## Workflow

The scripts must be executed in the order outlined below to retrieve LAI values:

1. Run PROSAIL simulations to generate the lookup-tables for the single Sentinel-2 and Planet SuperDove scenes to account for the viewing and illumination geometries.
   - for Sentinel-2: [run_prosail_sentinel2.py](run_prosail_sentinel2.py)
   - for PlanetScope: [run_prosail_planetscope.py](run_prosail_planetscope.py)
2. Invert the Sentinel-2 and PlanetScope scenes using the lookup-tables calculated in step 1:
   - for Sentinel-2: [lai_retrieval_sentinel2.py](lai_retrieval_sentinel2.py)
   - for PlanetScope: [lai_retrieval_planetscope.py](lai_retrieval_planetscope.py)
   - in the case of Sentinel-2, two results will be generated per scene:
      - one LAI result using the Sentinel-2 10 m bands only (B02, B03, B04, B08)
      - one LAI result using the Sentinel-2 20 m bands only (B05, B06, B07, B8A, B11, B12)

The `results` are placed in the data folder organized
```
| by platform (Sentinel-2 or PlanetScope)
   | year (currently there's only 2022)
      | month (e.g., 09_sep for September)
         | lai -> here you find the LAI data as GeoTiff
         | lut -> here you find the PROSAIL lookup tables
```

