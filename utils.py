#%%
import logging
import geojson
import xarray as xr
import re
import json
import openeo
from typing import Union
from pathlib import Path
import pytest

# Configure logging
_log = logging.getLogger(__name__)

def extract_test_geometries(filename) -> dict:
    """
    Read the geometries from a test file that is stored within the project
    :param filename: Name of the GeoJSON file to read
    :return: GeoJSON Geometry collection
    """
    path = f'./geofiles/{filename}'
    _log.info(f'Reading geometries from {path}')

    try:
        with open(path) as f:
            geometry_collection = geojson.load(f)
        return geometry_collection
    
    except Exception as e:
        _log.error(f'Error while reading geometries from {path}: {e}')
        raise

def extract_reference_band_statistics(scenario_name: str) -> dict:
    """
    Loads reference data from a JSON file for a specific scenario.

    Parameters:
        scenario_name (str): The name of the scenario for which reference data is needed.

    Returns:
        dict: The reference data for the specified scenario.
    """
    reference_file = 'groundtruth_regression_test.json'

    _log.info(f'Extracting reference band statistics for {scenario_name}')

    try:
        with open(reference_file, 'r') as file:
            all_reference_data = json.load(file)
        
        for scenario_data in all_reference_data:
            if scenario_data['scenario_name'] == scenario_name:
                return scenario_data['reference_data']
        
        raise ValueError(f"No reference data found for scenario '{scenario_name}' in file '{reference_file}'.")
    
    except Exception as e:
        _log.error(f"Error while extracting reference band statistics: {e}")
        raise

def assert_band_statistics(output_band_stats: dict, groundtruth_band_dict: dict, tolerance: float) -> None:
    """
    Compares and asserts the statistics of different bands in the output against the reference data.

    Parameters:
        output_band_stats (dict): The output dictionary containing band statistics to be compared.
        groundtruth_band_dict (dict): The reference dictionary containing expected band statistics.
        tolerance (float): Tolerance value for comparing values.

    Returns:
        None
    """
    _log.info('Comparing and asserting the statistics of different bands in the output')
    for output_band_name, output_band_stats in output_band_stats.items():
        if output_band_name not in groundtruth_band_dict:
            msg = f"Warning: Band '{output_band_name}' not found in reference."
            _log.warning(msg)
            continue

        gt_band_stats = groundtruth_band_dict[output_band_name]
        for stat, gt_value in gt_band_stats.items():
            if stat not in output_band_stats:
                msg = f"Warning: Statistic '{stat}' not found for band '{output_band_name}' in output."
                _log.warning(msg)
                continue

            _log.info(f"Assertion: Band '{output_band_name}' and statistic '{stat}'")
            output_stat = output_band_stats[stat]
            assert output_stat == pytest.approx(gt_value, rel=tolerance)

def calculate_band_statistics(hypercube: xr.Dataset) -> dict:
    """
    Calculate statistics for each variable in the output cube.
    
    Parameters:
        hypercube (xarray.Dataset): Input hypercube obtained through opening a netCDF file using xarray.Dataset.
        
    Returns:
        dict: A dictionary containing statistics for each variable in the output cube. Keys are variable names 
              (matching the pattern 'B01, B02, ...') and values are dictionaries containing mean, variance, min, max, 
              and quantile statistics.
    """
    statistics = {}
    band_names = [band_name for band_name in hypercube.data_vars if band_name != 'crs']

    for band_name in band_names:
        band_data = hypercube[band_name]
        mean_value = float(band_data.mean())
        variance_value = float(band_data.var())
        min_value = float(band_data.min())
        max_value = float(band_data.max())
        quantiles = band_data.quantile([0.25, 0.5, 0.75]).values
        
        statistics[band_name] = {
            'mean': mean_value,
            'variance': variance_value,
            'min': min_value,
            'max': max_value,
            'quantile25': quantiles[0],
            'quantile50': quantiles[1],
            'quantile75': quantiles[2],
        }

    return statistics

def execute_and_assert(cube: openeo.DataCube, 
                       output_path: Union[str, Path], 
                       scenario_name: str,
                       tolerance: float = 0.01) -> None:
    """
    Execute the provided OpenEO cube, save the result to the output path, 
    and assert its statistics against the reference data.

    Parameters:
        cube (openeo.datacube.DataCube): The OpenEO data cube to execute.
        output_path (Union[str, Path]): The path where the output should be saved.
        scenario_name (str): A name identifying the scenario for reference data.

    Returns:
        None

    Raises:
        RuntimeError: If there is an issue during execution, file saving, or assertion.
    """
    try:
        cube.execute_batch(output_path,
                            title=scenario_name,
                            description='benchmarking-creo', 
                            job_options={'driver-memory': '1g'}
                            )

        output_cube = xr.open_dataset(output_path)
        output_band_stats = calculate_band_statistics(output_cube)
        groundtruth_band_stats = extract_reference_band_statistics(scenario_name)
        assert_band_statistics(output_band_stats, groundtruth_band_stats, tolerance)
    except Exception as e:
        _log.error(f"Error during execution and assertion: {e}")
        raise



