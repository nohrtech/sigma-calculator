#!/usr/bin/env python3
"""
NohrTech Sigma Calculator - SBF Parser Module
A professional GNSS position accuracy analysis tool by NohrTech AS.

This module provides functionality to parse Septentrio Binary Format (SBF) files,
extracting position and accuracy information for analysis.

Author: NohrTech AS
"""

import struct
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import math
import binascii

class SBFParser:
    # Block types
    MEAS_BLOCK = 0x1703      # Measurement block
    CONFIG_BLOCK = 0x970e    # Configuration block
    PVT_BLOCK = 0x0fa2       # PVTGeodetic block
    
    # Satellite system identifiers
    SAT_SYSTEMS = {
        0: 'G',  # GPS
        1: 'R',  # GLONASS
        2: 'E',  # Galileo
        3: 'C',  # BeiDou
        4: 'S',  # SBAS
        5: 'J'   # QZSS
    }
    
    def __init__(self, filename: str):
        self.filename = filename
        self.blocks: List[Dict] = []
        self.header_info: Dict = {
            'file_type': 'SBF',
            'version': 1.0
        }

    def parse_file(self) -> List[Dict]:
        """Parse the SBF file and return list of blocks."""
        try:
            with open(self.filename, 'rb') as f:
                data = f.read()
                
            print(f"File size: {len(data)} bytes")
                
            # Find all sync markers
            positions = [i for i in range(len(data)-1) if data[i:i+2] == b'$@']
            print(f"Found {len(positions)} sync markers")
            
            for pos in positions:
                try:
                    block = self._parse_block(data[pos:])
                    if block:
                        print(f"Found block ID: 0x{block['id']:04x} at position {pos}")
                        processed_block = self._process_block(block)
                        if processed_block:
                            self.blocks.append(processed_block)
                except Exception as e:
                    print(f"Error processing block at position {pos}: {str(e)}")
                    continue
                    
            print(f"Successfully processed {len(self.blocks)} blocks")
            return self.blocks
        except Exception as e:
            raise ValueError(f"Error parsing SBF file: {str(e)}")

    def _parse_block(self, data: bytes) -> Optional[Dict]:
        """Parse a single SBF block."""
        if len(data) < 8:  # Minimum block size
            return None
            
        try:
            # Skip sync bytes
            crc = struct.unpack('<H', data[2:4])[0]
            id_length = struct.unpack('<H', data[4:6])[0]
            
            # Extract block ID and length
            block_id = id_length & 0x1FFF
            block_length = id_length >> 13
            if block_length == 0:
                block_length = struct.unpack('<H', data[6:8])[0]
                
            if block_length < 8 or block_length > len(data):
                return None
                
            return {
                'id': block_id,
                'length': block_length,
                'data': data[8:block_length]  # Skip header bytes
            }
        except struct.error:
            return None

    def _process_block(self, block: Dict) -> Optional[Dict]:
        """Process a parsed block based on its ID."""
        if block['id'] == self.PVT_BLOCK:
            return self._process_pvt_block(block)
        return None

    def _process_pvt_block(self, block: Dict) -> Optional[Dict]:
        """Process a PVTGeodetic block."""
        data = block['data']
        if len(data) < 92:  # Need at least up to accuracy values
            print(f"PVT block too short: {len(data)} bytes")
            return None
            
        try:
            # Read header fields
            tow = struct.unpack('<I', data[0:4])[0] / 1000.0  # Convert ms to seconds
            week = struct.unpack('<H', data[4:6])[0]
            mode = data[6]
            error = data[7]
            
            # Read position data (double precision floating point)
            lat = struct.unpack('<d', data[8:16])[0]  # Latitude in radians
            lon = struct.unpack('<d', data[16:24])[0]  # Longitude in radians
            height = struct.unpack('<d', data[24:32])[0]  # Height in meters
            
            # Read accuracies
            # Accuracies are stored at offsets 92 and 96 from block start
            # The block header is 8 bytes, so we need to subtract that
            h_accuracy_offset = 92 - 8
            v_accuracy_offset = 96 - 8
            
            # Check if we have enough data for accuracies
            if len(data) >= v_accuracy_offset + 4:
                try:
                    # Read raw bytes
                    h_raw = data[h_accuracy_offset:h_accuracy_offset+4]
                    v_raw = data[v_accuracy_offset:v_accuracy_offset+4]
                    
                    # Convert from 32-bit unsigned integer format
                    h_int = int.from_bytes(h_raw, byteorder='little', signed=False)
                    v_int = int.from_bytes(v_raw, byteorder='little', signed=False)
                    
                    # Scale factor: assuming Q8.24 fixed-point format
                    # Upper 8 bits are integer part, lower 24 bits are fraction
                    h_accuracy = (h_int >> 24) + ((h_int & 0xFFFFFF) / 16777216.0)  # Convert to meters
                    v_accuracy = (v_int >> 24) + ((v_int & 0xFFFFFF) / 16777216.0)  # Convert to meters
                    
                    print(f"Raw accuracy bytes: h={h_raw.hex()}, v={v_raw.hex()}")
                    print(f"Integer values: h={h_int}, v={v_int}")
                    print(f"Converted accuracies (m): h={h_accuracy}, v={v_accuracy}")
                except (struct.error, ValueError) as e:
                    print(f"Error parsing accuracies: {str(e)}")
                    h_accuracy = 0
                    v_accuracy = 0
            else:
                h_accuracy = 0
                v_accuracy = 0
            
            # Convert accuracies to East, North components (approximate)
            # Horizontal accuracy is split equally between East and North
            sigma_east = h_accuracy / math.sqrt(2) if h_accuracy > 0 else 0
            sigma_north = h_accuracy / math.sqrt(2) if h_accuracy > 0 else 0
            sigma_up = v_accuracy if v_accuracy > 0 else 0
            
            # Convert TOW to GPS week seconds
            gps_epoch = datetime(1980, 1, 6)  # GPS time epoch
            week_seconds = week * 7 * 24 * 3600
            timestamp = gps_epoch + timedelta(seconds=week_seconds + tow)
            
            # Convert coordinates to degrees
            # For latitude, first normalize to [-pi/2, pi/2]
            lat = lat % (2 * math.pi)  # Normalize to [0, 2pi]
            if lat > math.pi:
                lat = lat - 2 * math.pi  # Convert to [-pi, pi]
            if lat > math.pi/2:
                lat = math.pi - lat  # Convert to [-pi/2, pi/2]
            elif lat < -math.pi/2:
                lat = -math.pi - lat  # Convert to [-pi/2, pi/2]
                
            # For longitude, normalize to [-pi, pi]
            lon = lon % (2 * math.pi)  # Normalize to [0, 2pi]
            if lon > math.pi:
                lon = lon - 2 * math.pi  # Convert to [-pi, pi]
            
            lat_deg = math.degrees(lat)
            lon_deg = math.degrees(lon)
            
            # Print debug info
            print(f"Block at {block['data'][:8].hex()}")
            print(f"TOW={tow}, Week={week}, Mode={mode:02x}, Error={error:02x}")
            print(f"Raw lat={lat}, lon={lon}, height={height}")
            print(f"Deg lat={lat_deg}, lon={lon_deg}")
            print(f"Raw accuracies: h={h_accuracy}, v={v_accuracy}")
            
            return {
                'block_name': 'PVTGeodetic',
                'TOW': tow,
                'timestamp': timestamp,
                'mode': mode,
                'error': error,
                'lat': lat_deg,
                'lon': lon_deg,
                'height': height,
                'sigma_east': sigma_east,
                'sigma_north': sigma_north,
                'sigma_up': sigma_up
            }
            
        except struct.error as e:
            print(f"Error parsing PVT block: {str(e)}")
            return None
