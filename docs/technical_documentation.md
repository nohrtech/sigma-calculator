# GNSS Sigma Calculator - Technical Documentation

## Overview

The GNSS Sigma Calculator is a Python-based tool designed for analyzing measurement uncertainties in GNSS data. It provides statistical analysis of position accuracy and data quality across multiple GNSS data formats.

## Architecture

### Core Components

1. **GNSSSigmaCalculator Class**
   - Main class handling all file processing and calculations
   - Implements format-specific parsers and analysis methods
   - Manages unit conversions and coordinate transformations

2. **File Format Handlers**
   - Specialized methods for each supported file format
   - Automatic format detection based on file extensions
   - Robust error handling and data validation

3. **Statistical Analysis Engine**
   - Calculates standard deviations and means
   - Analyzes data distribution characteristics
   - Compares actual vs. theoretical normal distributions

## File Format Specifications

### 1. RINEX Format (*.rnx, *.obs)

#### Version Support
- Primary focus on RINEX 3.x
- Handles mixed observation files
- Supports multiple GNSS constellations (currently focused on GPS)

#### Header Processing
```
RINEX VERSION / TYPE
SYS / # / OBS TYPES
END OF HEADER
```

#### Observation Types
- C1* (C1C, C1P, etc.): L1 pseudorange
- P1*: L1 precise pseudorange
- C2*: L2 pseudorange
- P2*: L2 precise pseudorange

#### Data Structure
```
> EPOCH RECORD
G01 [observations...]  # GPS satellite 1
G02 [observations...]  # GPS satellite 2
...
```

### 2. LLH Format (*.llh)

#### File Structure
```
TIMESTAMP LAT LON HEIGHT STATUS SATS σLAT σLON σHEIGHT [additional]
```

#### Units
- Latitude/Longitude: Degrees
- Height: Meters
- Standard Deviations: 
  - Input: Degrees for lat/lon, meters for height
  - Output: All converted to meters

#### Coordinate Conversions
- Latitude: 1° ≈ 111.32 km
- Longitude: 1° ≈ cos(lat) * 111.32 km
- Height: Direct meter values

### 3. XYZ Format (*.xyz)

#### File Structure
```
TIMESTAMP X Y Z [σX σY σZ] [additional]
```

#### Units
- All values in meters
- Direct processing without conversion
- Optional standard deviation columns

## Implementation Details

### 1. RINEX Processing

```python
def _read_rinex_file(self):
    """
    1. Parse header for observation types
    2. Extract GPS observations
    3. Process epoch by epoch
    4. Calculate statistics
    """
```

Key Features:
- Handles epoch flags (0: OK, 1: power failure, >1: special event)
- Processes multiple observation types per satellite
- Averages observations within epochs
- Converts to kilometers for reasonable sigma values

### 2. LLH Processing

```python
def _read_llh_file(self):
    """
    1. Read lat/lon/height values
    2. Convert uncertainties to meters
    3. Account for latitude in longitude conversion
    4. Calculate statistics
    """
```

Key Features:
- Automatic unit conversion
- Latitude-dependent scaling
- Handles provided uncertainty values
- Validates data consistency

### 3. XYZ Processing

```python
def _read_xyz_file(self):
    """
    1. Read X/Y/Z coordinates
    2. Extract provided uncertainties if available
    3. Calculate position statistics
    4. Analyze distribution
    """
```

Key Features:
- Direct coordinate processing
- Optional uncertainty handling
- 3D position analysis
- Distribution comparison

## Statistical Analysis

### 1. Standard Deviation Calculation
```python
sigma = np.std(values)
```

### 2. Distribution Analysis
```python
within_1sigma = np.sum(np.abs(values - mean) <= sigma) / len(values) * 100
within_2sigma = np.sum(np.abs(values - mean) <= 2*sigma) / len(values) * 100
```

### 3. Position Uncertainty
For 3D position:
```python
overall_sigma = np.sqrt(sigma_x**2 + sigma_y**2 + sigma_z**2)
```

## Error Handling

1. **File Format Errors**
   - Invalid file extensions
   - Malformed headers
   - Incorrect data columns

2. **Data Validation**
   - Missing values
   - Invalid numbers
   - Out-of-range values

3. **Processing Errors**
   - Invalid epochs
   - Conversion failures
   - Statistical computation errors

## Output Format

```
Results:
----------------------------------------
Number of measurements: <count>

[Component] Component:
Sigma (std dev):     <value> meters
Mean:                <value> [units]
Provided sigma:      <value> meters
Data within 1-sigma: <value>% (expected: 68.27%)
Data within 2-sigma: <value>% (expected: 95.45%)

Overall position sigma: <value> meters
```

## Performance Considerations

1. **Memory Management**
   - Efficient numpy array usage
   - Streaming file processing
   - Minimal data copying

2. **Computation Optimization**
   - Vectorized calculations
   - Pre-allocated arrays
   - Efficient string parsing

3. **Scalability**
   - Handles large data files
   - Memory-efficient epoch processing
   - Robust error recovery

## Future Enhancements

1. **Additional Features**
   - SBF file format support
   - Time series analysis
   - Graphical output
   - Multi-constellation support

2. **Performance Improvements**
   - Parallel processing
   - Optimized file I/O
   - Memory usage optimization

3. **Analysis Capabilities**
   - Advanced statistical methods
   - Outlier detection
   - Quality indicators
   - Correlation analysis

## Dependencies

- Python 3.6+
- NumPy: For numerical computations
- Standard library modules:
  - argparse: Command line interface
  - os: File operations
  - typing: Type hints

## Usage Examples

### 1. Basic Usage
```bash
python nohrtech_sigma.py input.rnx
```

### 2. Processing Different Formats
```bash
# RINEX file
python nohrtech_sigma.py data.rnx

# LLH file
python nohrtech_sigma.py position.llh

# XYZ file
python nohrtech_sigma.py coords.xyz
```

## Troubleshooting

1. **Common Issues**
   - File format detection failures
   - Invalid data formats
   - Memory limitations

2. **Solutions**
   - Verify file extensions
   - Check file format compliance
   - Use smaller data chunks

3. **Debug Tips**
   - Check file encoding
   - Validate data columns
   - Monitor memory usage
