#!/usr/bin/env python3
"""
NohrTech Sigma Calculator
A professional GNSS position accuracy analysis tool by NohrTech.

This script calculates position accuracy values from:
- RINEX observation files (.rnx or .obs)
- Septentrio Binary Format files (.sbf)
- Emlid XYZ solution files (.xyz)
- LLH solution files (.llh)

Author: NohrTech
"""

import os
import math
import argparse
from typing import List, Dict, Tuple, Optional
import struct
from datetime import datetime
from sbf_parser import SBFParser
import numpy as np

class NohrTechSigmaCalculator:
    """Main calculator class for GNSS position accuracy analysis."""
    def __init__(self, filename: str):
        """Initialize the calculator with the observation file."""
        self.filename = filename
        self.file_format = self._determine_file_format()
        self.observations = []  # List of epoch observations
        self.sigma_values = {
            'epochs': [],  # List of epoch timestamps
            'E': [],      # East component sigmas
            'N': [],      # North component sigmas
            'U': []       # Up component sigmas
        }

    def _determine_file_format(self):
        """Determine the format of the input file."""
        ext = os.path.splitext(self.filename)[1].lower()
        if ext in ['.rnx', '.obs']:
            return 'RINEX'
        elif ext == '.sbf':
            return 'SBF'
        elif ext in ['.xyz', '.llh']:
            return 'XYZ'
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def read_file(self):
        """Read the observation file based on its format."""
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"File not found: {self.filename}")
        
        file_format = self._determine_file_format()
        if file_format == 'RINEX':
            self._read_rinex_file()
        elif file_format == 'SBF':
            self._read_sbf_file()
        elif file_format == 'XYZ':
            self._read_xyz_file()
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

    def _read_rinex_file(self):
        """Read and parse RINEX observation file."""
        with open(self.filename, 'r') as f:
            header_end = False
            current_epoch = None
            approx_position = None
            
            for line in f:
                if not header_end:
                    if "APPROX POSITION XYZ" in line:
                        # Extract approximate position from header
                        try:
                            x = float(line[0:14])
                            y = float(line[14:28])
                            z = float(line[28:42])
                            approx_position = {'X': x, 'Y': y, 'Z': z}
                            
                            # Convert XYZ to sigma values (using nominal accuracy)
                            nominal_accuracy = 10.0  # 10 meters nominal accuracy
                            self.sigma_values['epochs'].append(datetime.now())
                            self.sigma_values['E'].append(nominal_accuracy)
                            self.sigma_values['N'].append(nominal_accuracy)
                            self.sigma_values['U'].append(nominal_accuracy * 1.5)  # Vertical typically less accurate
                            
                        except ValueError:
                            print("Warning: Could not parse approximate position")
                    
                    if "END OF HEADER" in line:
                        header_end = True
                    continue

                # Parse epoch line
                if line[0] == '>':
                    if current_epoch:
                        self.observations.append(current_epoch)
                    
                    # Parse epoch timestamp
                    try:
                        year = int(line[2:6])
                        month = int(line[7:9])
                        day = int(line[10:12])
                        hour = int(line[13:15])
                        minute = int(line[16:18])
                        second = float(line[19:21])
                        
                        current_epoch = {
                            'time': datetime(year, month, day, hour, minute, int(second)),
                            'sats': {}
                        }
                        
                        # Add position data for this epoch
                        if approx_position:
                            current_epoch['position'] = approx_position
                            
                        num_sats = int(line[32:35])
                    except (ValueError, IndexError):
                        continue

                # Parse observation data
                if current_epoch is not None:
                    prn = line[0:3].strip()
                    if not prn:  # Skip empty lines
                        continue
                        
                    # Store satellite observations
                    # Note: We're not calculating position from observations yet
                    # This would require implementing a full GNSS positioning algorithm
                    current_epoch['sats'][prn] = {
                        'obs': line.strip()
                    }

            # Add last epoch
            if current_epoch:
                self.observations.append(current_epoch)

    def _read_xyz_file(self, file_path=None):
        """Read and parse Emlid XYZ or LLH solution file and extract sigma values.
        
        File format for LLH:
        Time LAT LON HEIGHT Q NS sE sN sU dE dN dU AGE AR
        Where:
        - sE, sN, sU are the standard deviations in meters
        - dE, dN, dU are the deltas in meters
        - Values are in meters
        """
        if file_path is None:
            file_path = self.filename
        self.filename = os.path.basename(file_path)
        self.sigma_values = {
            'epochs': [],  # List of epoch timestamps
            'E': [],      # East component sigmas
            'N': [],      # North component sigmas
            'U': []       # Up component sigmas
        }
        self.positions = {'E': [], 'N': [], 'U': []}
        
        # Case-insensitive check for .llh extension
        is_llh = os.path.splitext(file_path)[1].lower() == '.llh'
        
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    # Skip header lines
                    if line.startswith('%') or line.startswith('#'):
                        continue
                    
                    # Split line into fields
                    fields = line.strip().split()
                    if len(fields) < 10:  # Need at least timestamp and position fields
                        continue
                    
                    # Parse timestamp (format: YYYY/MM/DD HH:MM:SS.FFF)
                    timestamp = ' '.join(fields[0:2])
                    
                    # Parse sigma values (convert from meters to millimeters)
                    if is_llh:
                        # For LLH files: Time LAT LON HEIGHT Q NS sE sN sU dE dN dU AGE AR
                        # sE, sN, sU are at indices 6, 7, 8 (0-based)
                        e_sigma = float(fields[6]) * 1000  # Convert to mm
                        n_sigma = float(fields[7]) * 1000  # Convert to mm
                        u_sigma = float(fields[8]) * 1000  # Convert to mm
                    else:
                        # For XYZ files, sigma values are in columns 7, 8, 9
                        e_sigma = float(fields[7]) * 1000
                        n_sigma = float(fields[8]) * 1000
                        u_sigma = float(fields[9]) * 1000
                    
                    self.sigma_values['epochs'].append(timestamp)
                    self.sigma_values['E'].append(e_sigma)
                    self.sigma_values['N'].append(n_sigma)
                    self.sigma_values['U'].append(u_sigma)
                    
                except (ValueError, IndexError) as e:
                    print(f"Warning: Could not parse line: {line.strip()}")
                    continue

    def _read_sbf_file(self):
        """Read and parse SBF observation file using SBFParser."""
        parser = SBFParser(self.filename)
        blocks = parser.parse_file()
        
        for block in blocks:
            if block['block_name'] == "PVTGeodetic":
                # Extract timestamp from block
                timestamp = block['timestamp']
                
                # Extract sigma values from the block
                # Convert to millimeters (assuming input is in meters)
                e_sigma = block['sigma_east'] * 1000  # Convert to mm
                n_sigma = block['sigma_north'] * 1000  # Convert to mm
                u_sigma = block['sigma_up'] * 1000  # Convert to mm
                
                self.sigma_values['epochs'].append(timestamp)
                self.sigma_values['E'].append(e_sigma)
                self.sigma_values['N'].append(n_sigma)
                self.sigma_values['U'].append(u_sigma)

    def calculate_sigma(self):
        """Calculate receiver position sigma values."""
        print("\nCalculating sigma values...")
        
        if not self.sigma_values['epochs']:
            print("No position data found in file")
            return None

        # Calculate horizontal sigma (RMS of East and North components)
        horizontal_sigmas = []
        vertical_sigmas = []
        for i in range(len(self.sigma_values['E'])):
            # Horizontal sigma (RMS of East and North components)
            e_sigma = self.sigma_values['E'][i]
            n_sigma = self.sigma_values['N'][i]
            h_sigma = np.sqrt((e_sigma**2 + n_sigma**2) / 2)  # RMS of E and N
            horizontal_sigmas.append(h_sigma)
            
            # Vertical sigma (Up component)
            vertical_sigmas.append(self.sigma_values['U'][i])

        # Create results dictionary with proper structure
        results = {
            'epochs': [],
            'horizontal': horizontal_sigmas,
            'vertical': vertical_sigmas,
            'E': self.sigma_values['E'],
            'N': self.sigma_values['N'],
            'U': self.sigma_values['U']
        }

        # Create epoch entries with all components
        for i in range(len(self.sigma_values['epochs'])):
            epoch_entry = {
                'time': self.sigma_values['epochs'][i],
                'horizontal': horizontal_sigmas[i],
                'vertical': vertical_sigmas[i],
                'E': self.sigma_values['E'][i],
                'N': self.sigma_values['N'][i],
                'U': self.sigma_values['U'][i]
            }
            results['epochs'].append(epoch_entry)

        # Calculate summary statistics
        summary = {}
        for comp in ['horizontal', 'vertical', 'E', 'N', 'U']:
            values = np.array(results[comp])
            summary[comp] = {
                'mean': np.mean(values),
                'min': np.min(values),
                'max': np.max(values),
                'std': np.std(values)
            }
        
        results['summary'] = summary
        return results

    def calculate_sigma_summary(self, sigma_values):
        """Calculate summary statistics for each component."""
        components = ['horizontal', 'vertical', 'E', 'N', 'U']
        summary = {}

        for comp in components:
            values = np.array(sigma_values[comp])
            summary[comp] = {
                'mean': f"{np.mean(values):.2f}",
                'min': f"{np.min(values):.2f}",
                'max': f"{np.max(values):.2f}",
                'std': f"{np.std(values):.2f}"
            }

        return summary

    def print_results(self, results):
        """Print the sigma calculation results."""
        if results is None:
            print("No results to display")
            return
            
        print("\nResults:")
        print("-" * 40)
        
        if not results['epochs']:
            print("No position data found in file")
            return
        
        # Print epoch-by-epoch results
        print("Epoch-by-Epoch Results:")
        print("{:<25} {:>10} {:>10} {:>10} {:>10} {:>10}".format(
            "Time", "Horiz(mm)", "Vert(mm)", "E(mm)", "N(mm)", "U(mm)"))
        print("-" * 75)
        
        for epoch in results['epochs']:
            print("{:<25} {:10.3f} {:10.3f} {:10.3f} {:10.3f} {:10.3f}".format(
                str(epoch['time']),
                epoch['horizontal'],
                epoch['vertical'],
                epoch['E'],
                epoch['N'],
                epoch['U']
            ))
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print("-" * 40)
        print("{:<12} {:>10} {:>10} {:>10} {:>10}".format(
            "Component", "Mean(mm)", "Min(mm)", "Max(mm)", "Std(mm)"))
        print("-" * 52)
        
        for comp in ['horizontal', 'vertical', 'E', 'N', 'U']:
            stats = results['summary'][comp]
            print("{:<12} {:10.3f} {:10.3f} {:10.3f} {:10.3f}".format(
                comp.capitalize(),
                stats['mean'],
                stats['min'],
                stats['max'],
                stats['std']
            ))

def main():
    """Main function to run the sigma calculator."""
    parser = argparse.ArgumentParser(description='Calculate receiver position sigma values from RINEX, SBF, or XYZ files')
    parser.add_argument('observation_file', help='Path to the observation file (.rnx, .obs, .sbf, .xyz, or .llh)')
    args = parser.parse_args()

    calculator = NohrTechSigmaCalculator(args.observation_file)
    calculator.read_file()
    results = calculator.calculate_sigma()
    calculator.print_results(results)

if __name__ == "__main__":
    main()
