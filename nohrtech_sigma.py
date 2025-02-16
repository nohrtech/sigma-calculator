"""GNSS Sigma Calculator

A versatile tool for analyzing GNSS measurement uncertainties and data distributions across multiple file formats.

This script provides comprehensive analysis of GNSS data, including:
- Standard deviation (sigma) calculation for each component
- Data distribution analysis within 1σ and 2σ ranges
- Comparison with provided uncertainty values (when available)
- Overall position uncertainty estimation
- Automatic unit conversion and scaling

Supported File Formats:
- RINEX 3.x Observation Files (*.rnx, *.obs)
  * Focuses on GPS pseudorange measurements
  * Handles multiple observation types (C1*, P1*, C2*, P2*)
  * Accounts for epoch flags and special events
- LLH Files (*.llh)
  * Format: Timestamp Lat Lon Height Status Sats σLat σLon σHeight [additional fields]
  * Automatically converts angular uncertainties to meters
  * Accounts for latitude-dependent scaling of longitude uncertainties
- XYZ Files (*.xyz)
  * Format: Timestamp X Y Z [σX σY σZ] [additional fields]
  * Direct processing of Cartesian coordinates
  * Supports files with or without provided uncertainties
- SBF Files (*.sbf) - Future support planned

Usage:
    python nohrtech_sigma.py <input_file>

Author: NohrtechGNSS
"""

import argparse
import numpy as np
from typing import Dict, Optional, List
import os

class GNSSSigmaCalculator:
    def __init__(self, filename: str):
        """Initialize the calculator with the input file."""
        self.filename = filename
        self.file_type = self._determine_file_type()
        
    def _determine_file_type(self) -> str:
        """Determine the file type based on extension."""
        ext = os.path.splitext(self.filename)[1].lower()
        if ext in ['.rnx', '.obs']:
            return 'rinex'
        elif ext == '.llh':
            return 'llh'
        elif ext == '.xyz':
            return 'xyz'
        elif ext == '.sbf':
            return 'sbf'
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    def read_file(self) -> np.ndarray:
        """Read and parse the GNSS data file."""
        print(f"Reading file: {self.filename}")
        
        # Detect file type from extension
        ext = os.path.splitext(self.filename)[1].lower()
        if ext == '.xyz':
            self.file_type = 'xyz'
            print("File type detected: XYZ")
            return self._read_xyz_file()
        elif ext == '.llh':
            self.file_type = 'llh'
            print("File type detected: LLH")
            return self._read_llh_file()
        elif ext == '.rnx' or ext == '.obs':
            self.file_type = 'rinex'
            print("File type detected: RINEX")
            return self._read_rinex_file()
        elif ext == '.sbf':
            self.file_type = 'sbf'
            print("File type detected: SBF")
            return self._read_sbf_file()
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _read_rinex_file(self) -> np.ndarray:
        """Read and parse RINEX observation file."""
        measurements = []
        rinex_version = None
        obs_types = []
        pseudorange_indices = []  # Indices of pseudorange observations (C1C, C1P, etc.)
        
        with open(self.filename, 'r') as f:
            # Parse header
            for line in f:
                if "RINEX VERSION" in line:
                    rinex_version = float(line[:9].strip())
                elif "SYS / # / OBS TYPES" in line:
                    # Get observation types for each system
                    if line[0] != " ":  # New satellite system
                        curr_sys = line[0]
                        num_obs = int(line[3:6])
                        obs = []
                        # Read observation types
                        while len(obs) < num_obs:
                            if len(obs) == 0:  # First line
                                obs.extend(line[7:60].strip().split())
                            else:  # Continuation lines
                                next_line = f.readline()
                                if "SYS / # / OBS TYPES" in next_line:  # Handle continuation marker
                                    obs.extend(next_line[7:60].strip().split())
                        
                        # Find pseudorange observations
                        for i, obs_type in enumerate(obs):
                            if obs_type.startswith(('C1', 'P1', 'C2', 'P2')):
                                pseudorange_indices.append(i)
                        
                        if curr_sys == 'G':  # Focus on GPS observations
                            obs_types = [(curr_sys, obs)]
                            break
                elif "END OF HEADER" in line:
                    break
            
            if not obs_types or not pseudorange_indices:
                raise ValueError("No suitable observation types found in RINEX file")
            
            # Parse observations
            epoch_data = []
            for line in f:
                try:
                    if line[0] == ">":  # Epoch line in RINEX 3
                        # Process previous epoch if we have data
                        if epoch_data:
                            # Calculate mean of valid pseudorange observations in epoch
                            valid_obs = [x for x in epoch_data if x is not None]
                            if valid_obs:
                                # Convert from meters to kilometers for more reasonable sigma values
                                measurements.append(np.mean(valid_obs) / 1000.0)
                            epoch_data = []
                        
                        # Check epoch flag (0: OK, 1: power failure, >1: special event)
                        epoch_flag = int(line[31])
                        if epoch_flag > 1:  # Skip special events
                            continue
                            
                        # Parse number of satellites
                        num_sats = int(line[32:35])
                        
                        # Skip satellite list lines if present
                        if num_sats > 12:
                            extra_lines = (num_sats - 1) // 12
                            for _ in range(extra_lines):
                                next(f)
                    else:
                        # Parse observation line
                        if rinex_version >= 3.0 and line[0] == 'G':  # GPS observations
                            # In RINEX 3, each line contains all observations for one satellite
                            obs_line = line.rstrip()
                            while len(obs_line) < 3 + 16*len(obs_types[0][1]):  # Pad incomplete lines
                                obs_line += " " * 16
                            
                            # Extract only pseudorange observations
                            for idx in pseudorange_indices:
                                if 3+16*idx+14 <= len(obs_line):
                                    obs_str = obs_line[3+16*idx:3+16*idx+14].strip()
                                    try:
                                        obs_val = float(obs_str)
                                        if obs_val > 0:  # Valid observation
                                            epoch_data.append(obs_val)
                                    except ValueError:
                                        continue
                        
                except (ValueError, IndexError) as e:
                    continue
            
            # Process last epoch
            if epoch_data:
                valid_obs = [x for x in epoch_data if x is not None]
                if valid_obs:
                    measurements.append(np.mean(valid_obs) / 1000.0)  # Convert to kilometers
        
        if not measurements:
            raise ValueError("No valid measurements found in RINEX file")
            
        return np.array(measurements)

    def _read_llh_file(self) -> np.ndarray:
        """Read and parse LLH (Latitude/Longitude/Height) file."""
        data = []
        with open(self.filename, 'r') as f:
            for line in f:
                try:
                    tokens = line.strip().split()
                    if len(tokens) >= 9:  # We need at least up to the standard deviations
                        # Time is in tokens[0-1]
                        lat = float(tokens[2])  # Latitude
                        lon = float(tokens[3])  # Longitude
                        h = float(tokens[4])    # Height
                        # Status and number of satellites in tokens[5-6]
                        # Standard deviations in tokens[7-9]
                        lat_std = float(tokens[7])  # Lat std
                        lon_std = float(tokens[8])  # Lon std
                        h_std = float(tokens[9])    # Height std
                        data.append([lat, lon, h, lat_std, lon_std, h_std])
                except (ValueError, IndexError) as e:
                    continue
        return np.array(data)

    def _read_xyz_file(self) -> np.ndarray:
        """Read and parse XYZ (Cartesian coordinates) file."""
        data = []
        with open(self.filename, 'r') as f:
            for line in f:
                try:
                    tokens = line.strip().split()
                    if len(tokens) >= 9:  # We need at least up to the standard deviations
                        # Time is in tokens[0-1]
                        x = float(tokens[2])  # X coordinate
                        y = float(tokens[3])  # Y coordinate
                        z = float(tokens[4])  # Z coordinate
                        # Status and number of satellites in tokens[5-6]
                        # Standard deviations in tokens[7-9]
                        x_std = float(tokens[7])  # X std
                        y_std = float(tokens[8])  # Y std
                        z_std = float(tokens[9])  # Z std
                        data.append([x, y, z, x_std, y_std, z_std])
                except (ValueError, IndexError) as e:
                    continue
        return np.array(data)

    def _read_sbf_file(self) -> np.ndarray:
        """Read and parse SBF (Septentrio Binary Format) file."""
        raise NotImplementedError("SBF file parsing is not yet implemented")

    def calculate_sigma(self, data: np.ndarray) -> Dict:
        """
        Calculate sigma (standard deviation) for the GNSS measurements.
        Also analyzes data distribution within 1σ and 2σ ranges.
        """
        if len(data) == 0:
            return {
                'count': 0,
                'components': {},
                'overall_sigma': 0.0
            }

        results = {
            'count': len(data),
            'components': {},
            'overall_sigma': 0.0
        }

        if self.file_type == 'llh':
            components = ['Latitude', 'Longitude', 'Height']
            for i, comp in enumerate(components):
                values = data[:, i]
                
                # For lat/lon, convert to meters for meaningful statistics
                if comp == 'Latitude':
                    # 1 degree latitude ≈ 111.32 km at equator
                    scale = 111320  # meters per degree
                    values_m = (values - np.mean(values)) * scale
                    sigma = np.std(values_m)
                    # Convert provided sigma from degrees to meters
                    provided_sigma = data[:, i+3] * scale if data.shape[1] > 5 else None
                    min_sigma = np.min(provided_sigma) if provided_sigma is not None else None
                    max_sigma = np.max(provided_sigma) if provided_sigma is not None else None
                    provided_sigma = np.mean(provided_sigma) if provided_sigma is not None else None
                elif comp == 'Longitude':
                    # 1 degree longitude ≈ cos(lat) * 111.32 km
                    lat_rad = np.mean(data[:, 0]) * np.pi / 180
                    scale = np.cos(lat_rad) * 111320  # meters per degree at this latitude
                    values_m = (values - np.mean(values)) * scale
                    sigma = np.std(values_m)
                    # Convert provided sigma from degrees to meters
                    provided_sigma = data[:, i+3] * scale if data.shape[1] > 5 else None
                    min_sigma = np.min(provided_sigma) if provided_sigma is not None else None
                    max_sigma = np.max(provided_sigma) if provided_sigma is not None else None
                    provided_sigma = np.mean(provided_sigma) if provided_sigma is not None else None
                else:  # Height
                    values_m = values
                    sigma = np.std(values)
                    provided_sigma = np.mean(data[:, i+3]) if data.shape[1] > 5 else None
                    min_sigma = np.min(data[:, i+3]) if data.shape[1] > 5 else None
                    max_sigma = np.max(data[:, i+3]) if data.shape[1] > 5 else None
                
                # Calculate percentage of data within 1σ and 2σ
                if comp in ['Latitude', 'Longitude']:
                    within_1sigma = np.sum(np.abs(values_m) <= sigma) / len(values) * 100
                    within_2sigma = np.sum(np.abs(values_m) <= 2*sigma) / len(values) * 100
                else:
                    within_1sigma = np.sum(np.abs(values - np.mean(values)) <= sigma) / len(values) * 100
                    within_2sigma = np.sum(np.abs(values - np.mean(values)) <= 2*sigma) / len(values) * 100
                
                results['components'][comp] = {
                    'sigma': sigma,
                    'mean': np.mean(values),
                    'provided_sigma': provided_sigma,
                    'min_provided_sigma': min_sigma,
                    'max_provided_sigma': max_sigma,
                    'within_1sigma': within_1sigma,
                    'within_2sigma': within_2sigma
                }
            
            # Calculate 3D position sigma
            lat_sigma = results['components']['Latitude']['sigma']
            lon_sigma = results['components']['Longitude']['sigma']
            h_sigma = results['components']['Height']['sigma']
            results['overall_sigma'] = np.sqrt(lat_sigma**2 + lon_sigma**2 + h_sigma**2)

        elif self.file_type == 'xyz':
            components = ['X', 'Y', 'Z']
            for i, comp in enumerate(components):
                values = data[:, i]
                sigma = np.std(values)
                mean = np.mean(values)
                
                # Calculate percentage of data within 1σ and 2σ
                within_1sigma = np.sum(np.abs(values - mean) <= sigma) / len(values) * 100
                within_2sigma = np.sum(np.abs(values - mean) <= 2*sigma) / len(values) * 100
                
                # Get the provided standard deviation from the file (columns 3-5 after XYZ)
                provided_sigma = np.mean(data[:, i+3]) if data.shape[1] > 5 else None
                
                results['components'][comp] = {
                    'sigma': sigma,
                    'mean': mean,
                    'provided_sigma': provided_sigma,
                    'within_1sigma': within_1sigma,
                    'within_2sigma': within_2sigma,
                    'min_provided_sigma': np.min(data[:, i+3]) if data.shape[1] > 5 else None,
                    'max_provided_sigma': np.max(data[:, i+3]) if data.shape[1] > 5 else None
                }
            
            # Calculate overall position sigma (RMS of component sigmas)
            sigmas = [results['components'][c]['sigma'] for c in components]
            results['overall_sigma'] = np.sqrt(np.sum(np.square(sigmas)))
            
            # Calculate 3D position deviations
            position_deviations = np.sqrt(np.sum(np.square(data[:, :3] - np.mean(data[:, :3], axis=0)), axis=1))
            position_sigma = np.std(position_deviations)
            
            # Calculate percentage of 3D positions within 1σ and 2σ
            within_1sigma_3d = np.sum(position_deviations <= position_sigma) / len(position_deviations) * 100
            within_2sigma_3d = np.sum(position_deviations <= 2*position_sigma) / len(position_deviations) * 100
            
            results['position_analysis'] = {
                'sigma': position_sigma,
                'within_1sigma': within_1sigma_3d,
                'within_2sigma': within_2sigma_3d
            }

        else:  # RINEX or other single-measurement types
            values = data
            sigma = np.std(values)
            mean = np.mean(values)
            within_1sigma = np.sum(np.abs(values - mean) <= sigma) / len(values) * 100
            within_2sigma = np.sum(np.abs(values - mean) <= 2*sigma) / len(values) * 100
            results['overall_sigma'] = sigma
            results['mean'] = mean
            results['within_1sigma'] = within_1sigma
            results['within_2sigma'] = within_2sigma

        return results

    def print_results(self, results: Dict):
        """Print the analysis results."""
        print("\nResults:")
        print("-" * 40)
        print(f"Number of measurements: {results['count']}")
        
        if results['count'] > 0:
            if 'components' in results and results['components']:
                for comp, stats in results['components'].items():
                    if self.file_type == 'llh':
                        if comp == 'Latitude':
                            print(f"\nLatitude Component:")
                        elif comp == 'Longitude':
                            print(f"\nLongitude Component:")
                        elif comp == 'Height':
                            print(f"\nHeight Component:")
                    else:
                        print(f"\n{comp} Component:")
                        
                    if comp in ['Latitude', 'Longitude']:
                        print(f"Sigma (std dev):     {stats['sigma']:.3f} meters")
                        print(f"Mean:                {stats['mean']:.8f} degrees")
                        if 'provided_sigma' in stats and stats['provided_sigma'] is not None:
                            print(f"Provided sigma:      {stats['provided_sigma']:.3f} meters")
                            print(f"Min provided sigma:  {stats['min_provided_sigma']:.3f} meters")
                            print(f"Max provided sigma:  {stats['max_provided_sigma']:.3f} meters")
                    else:  # Height or XYZ components
                        print(f"Sigma (std dev):     {stats['sigma']:.3f} meters")
                        print(f"Mean:                {stats['mean']:.3f} meters")
                        if 'provided_sigma' in stats and stats['provided_sigma'] is not None:
                            print(f"Provided sigma:      {stats['provided_sigma']:.3f} meters")
                            print(f"Min provided sigma:  {stats['min_provided_sigma']:.3f} meters")
                            print(f"Max provided sigma:  {stats['max_provided_sigma']:.3f} meters")
                    
                    print(f"Data within 1-sigma: {stats['within_1sigma']:.1f}% (expected: 68.27%)")
                    print(f"Data within 2-sigma: {stats['within_2sigma']:.1f}% (expected: 95.45%)")
            
            if 'position_analysis' in results:
                print(f"\n3D Position Analysis:")
                print(f"Position sigma:      {results['position_analysis']['sigma']:.3f} meters")
                print(f"Positions within 1-sigma: {results['position_analysis']['within_1sigma']:.1f}% (expected: 68.27%)")
                print(f"Positions within 2-sigma: {results['position_analysis']['within_2sigma']:.1f}% (expected: 95.45%)")
            
            if results.get('overall_sigma', 0) > 0:
                print(f"\nOverall position sigma: {results['overall_sigma']:.3f} meters")
                print(f"Data within 1-sigma: {results['within_1sigma']:.1f}% (expected: 68.27%)")
                print(f"Data within 2-sigma: {results['within_2sigma']:.1f}% (expected: 95.45%)")

def main():
    parser = argparse.ArgumentParser(
        description='Calculate sigma values from GNSS measurement files')
    parser.add_argument('file', help='Input GNSS data file')
    args = parser.parse_args()
    
    try:
        calculator = GNSSSigmaCalculator(args.file)
        data = calculator.read_file()
        results = calculator.calculate_sigma(data)
        calculator.print_results(results)
            
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
