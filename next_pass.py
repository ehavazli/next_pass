#!/usr/bin/env python3

import argparse
import logging

from shapely.geometry import Point, box

from landsat_pass import next_landsat_pass
from sentinel_pass import (next_sentinel_pass,
                           create_s1_collection_plan,
                           create_s2_collection_plan)
from utils import bbox_type, create_polygon_from_kml

LOGGER = logging.getLogger("next_pass")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for CLI inputs."""
    parser = argparse.ArgumentParser(description="Find next satellite overpass date.")
    parser.add_argument(
        "-b", "--bbox", required=True, type=float, nargs=4,
        metavar=("lat_min", "lat_max", "lon_min", "lon_max"),
        help="Bounding box coordinates (SNWE order). A point has equal SN and EW."
    )
    parser.add_argument(
        "-s", "--sat", default="all",
        choices=["sentinel-1", "sentinel-2", "landsat", "all"],
        help="Satellite mission. Default is all."
    )
    parser.add_argument(
        "-f", "--aoi-file", type=str,
        help="Optional path to a KML file defining the AOI polygon."
    )
    parser.add_argument(
        "-l", "--log_level", default="info",
        choices=["debug", "info", "warning", "error"],
        help="Set logging level (default: info)."
    )
    return parser


def find_next_overpass(args) -> dict:
    """Main logic for finding the next satellite overpasses."""
    lat_min, lat_max, lon_min, lon_max = bbox_type(args.bbox)

    if args.aoi_file:
        geometry = create_polygon_from_kml(args.aoi_file)
    elif lat_min == lat_max and lon_min == lon_max:
        geometry = Point(lon_min, lat_min)
    else:
        geometry = box(lon_min, lat_min, lon_max, lat_max)

    if args.sat == "all":
        LOGGER.info("Fetching Sentinel-1 data...")
        sentinel1 = next_sentinel_pass(create_s1_collection_plan, geometry)

        LOGGER.info("Fetching Sentinel-2 data...")
        sentinel2 = next_sentinel_pass(create_s2_collection_plan, geometry)

        LOGGER.info("Fetching Landsat data...")
        landsat = next_landsat_pass(lat_min, lon_min)

        return {
            "sentinel-1": sentinel1,
            "sentinel-2": sentinel2,
            "landsat": landsat,
        }

    if args.sat == "sentinel-1":
        LOGGER.info("Fetching Sentinel-1 data...")
        return next_sentinel_pass(create_s1_collection_plan, geometry)

    if args.sat == "sentinel-2":
        LOGGER.info("Fetching Sentinel-2 data...")
        return next_sentinel_pass(create_s2_collection_plan, geometry)

    if args.sat == "landsat":
        LOGGER.info("Fetching Landsat data...")
        return next_landsat_pass(lat_min, lon_min)

    raise ValueError(
        "Satellite not recognized. "
        "Supported values: sentinel-1, sentinel-2, landsat, all."
    )


def main():
    """Main entry point."""
    args = create_parser().parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    result = find_next_overpass(args)

    if isinstance(result, dict) and "sentinel-1" in result:
        # Case: satellite == all
        for mission, mission_result in result.items():
            print(f"\n=== {mission.upper()} ===")
            print(mission_result.get("next_collect_info",
                                     "No collection info available."))
    else:
        # Case: only one satellite selected
        print(result.get("next_collect_info", "No collection info available."))


if __name__ == "__main__":
    main()
