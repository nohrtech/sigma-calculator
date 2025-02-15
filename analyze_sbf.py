#!/usr/bin/env python3
"""
NohrTech Sigma Calculator - SBF File Analyzer
A professional GNSS position accuracy analysis tool by NohrTech AS.

This utility examines the structure of Septentrio Binary Format (SBF) files
to determine block types and data formats.

Author: NohrTech AS
"""

import struct
from collections import Counter
import binascii

def analyze_sbf(filename):
    block_ids = Counter()
    block_lengths = Counter()
    sync_positions = []
    last_pos = 0
    
    with open(filename, 'rb') as f:
        data = f.read()
        
    # Find all sync markers
    print("\nAnalyzing sync markers...")
    sync_positions = [i for i in range(len(data)-1) if data[i:i+2] == b'$@']
    if sync_positions:
        print(f"Found {len(sync_positions)} potential sync markers")
        
        # Analyze distances between sync markers
        distances = [sync_positions[i+1] - sync_positions[i] for i in range(len(sync_positions)-1)]
        if distances:
            print(f"Most common distances between sync markers: {Counter(distances).most_common(3)}")
    else:
        print("No standard sync markers found")
        
    # Try to identify block structure
    print("\nAnalyzing potential blocks...")
    for pos in sync_positions[:10]:  # Analyze first 10 blocks
        try:
            # Skip sync bytes
            block_start = pos + 2
            
            # Read potential header fields
            if block_start + 8 <= len(data):
                crc = struct.unpack('<H', data[block_start:block_start+2])[0]
                id_length = struct.unpack('<H', data[block_start+2:block_start+4])[0]
                next_bytes = data[block_start+4:block_start+8]
                
                print(f"\nBlock at position {pos}:")
                print(f"CRC: {crc}")
                print(f"ID/Length: {hex(id_length)}")
                print(f"Next 4 bytes: {binascii.hexlify(next_bytes)}")
                
                # Try different length calculations
                lengths = [
                    ("Raw", id_length),
                    ("Shifted", id_length >> 13),
                    ("Masked", id_length & 0x1FFF),
                ]
                
                print("Potential lengths:")
                for name, length in lengths:
                    print(f"  {name}: {length}")
                
                # Show sample of data
                if block_start + 32 <= len(data):
                    print(f"First 32 bytes: {binascii.hexlify(data[block_start:block_start+32])}")
        except Exception as e:
            print(f"Error analyzing block at {pos}: {str(e)}")
    
    print("\nFile analysis complete")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python analyze_sbf.py <sbf_file>")
        sys.exit(1)
    
    analyze_sbf(sys.argv[1])
