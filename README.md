# NohrTech Sigma Calculator

A professional GNSS position accuracy analysis tool by NohrTech.

## Features

- Calculate sigma values from RINEX observation files
- Support for Septentrio Binary Format (SBF) files
- Support for Emlid XYZ and LLH solution files
- Generate PDF reports with sigma statistics
- Web interface for easy file upload and analysis
- Detailed epoch-by-epoch analysis for XYZ/LLH files
- Summary statistics including mean, min, max, and standard deviation
- Advanced accuracy calculations:
  - Horizontal sigma: RMS of East and North components per epoch
  - Vertical sigma: RMS of Up component value per epoch
  - Individual epoch-by-epoch analysis for all components
  - Statistical analysis across all epochs
- Open results in a new tab for better viewing and comparison
- Process multiple files in separate tabs
- Compare sigma results between two files:
  - View individual statistics for each file
  - Calculate absolute and percentage differences
  - Color-coded comparison results for easy interpretation

## Supported File Formats

1. RINEX Observation Files
   - File extensions: .rnx, .obs
   - Contains raw GNSS observation data

2. Septentrio Binary Format (SBF)
   - File extension: .sbf
   - Binary format containing GNSS measurements

3. Emlid Solution Files
   - File extensions: .xyz, .llh
   - Position solution files from Emlid GNSS receivers
   - Contains epoch-by-epoch position data with accuracy metrics
   - Supports both XYZ (Cartesian) and LLH (Latitude/Longitude/Height) formats

## Installation

### Option 1: Quick Installation (Debian 12)

1. Run this single command:
   ```bash
   wget -O- https://raw.githubusercontent.com/nohrtech/sigma-calculator/master/install.sh | sudo bash
   ```

2. The application will be automatically installed and configured with Apache. Once installation is complete, you can access it at:
   ```
   http://localhost
   ```

### Option 2: From Git Repository

1. Clone the repository:
   ```bash
   git clone https://github.com/nohrtech/sigma-calculator.git
   cd sigma-calculator
   ```

2. Make the installation script executable and run it:
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

3. Access the application at:
   ```
   http://localhost
   ```

### Option 3: Manual Installation (Development)

1. Clone the repository:
   ```bash
   git clone https://github.com/nohrtech/sigma-calculator.git
   cd sigma-calculator
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   .\venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create required directories:
   ```bash
   mkdir -p uploads instance
   chmod 755 uploads instance  # On Linux/Mac
   # or
   mkdir uploads instance      # On Windows
   ```

5. Start the development server:
   ```bash
   python app.py
   ```

6. Access the development server at:
   ```
   http://localhost:5000
   ```


### Development Workflow

We use a branching workflow for development:

1. Development happens in the `development` branch
2. Stable code is in the `master` branch
3. For new features:
   ```bash
   git checkout development   # Switch to development branch
   git pull origin master    # Get latest changes
   # Make your changes
   git add .                 # Stage changes
   git commit -m "Description"
   git push origin development
   ```
4. To update master:
   ```bash
   git checkout master
   git merge development
   git push origin master
   ```

## Deployment Notes

The application is set up to run under Apache with mod_wsgi. After installation:

- Application files are in `/var/www/sigma-calculator`
- Apache logs are in `/var/log/apache2/sigma-calculator-{error,access}.log`

### Updating the Application

There are two ways to update the application:

#### Option 1: Using the Update Script (Recommended)

The update script provides an automated way to update the application with built-in safety features:
- Creates a backup before updating
- Checks Apache status after update
- Monitors for errors
- Provides rollback instructions

To use the update script:

1. Make the script executable:
   ```bash
   sudo chmod +x /var/www/sigma-calculator/update.sh
   ```

2. Run the script:
   ```bash
   sudo /var/www/sigma-calculator/update.sh
   ```

The script will:
- Create a backup of the current installation
- Pull the latest changes from Git
- Update file permissions
- Restart Apache
- Check for any errors
- Provide rollback instructions if needed

#### Option 2: Manual Update

If you prefer to update manually, follow these steps:

1. Navigate to the application directory:
   ```bash
   cd /var/www/sigma-calculator
   ```

2. Pull the latest changes:
   ```bash
   sudo git pull origin master
   ```

3. Update file permissions:
   ```bash
   sudo chown -R www-data:www-data /var/www/sigma-calculator
   sudo chmod -R 755 /var/www/sigma-calculator
   ```

4. Restart Apache to apply changes:
   ```bash
   sudo systemctl restart apache2
   ```

5. Check Apache status (optional):
   ```bash
   sudo systemctl status apache2
   ```

6. View logs for any errors (optional):
   ```bash
   sudo tail -f /var/log/apache2/sigma-calculator-error.log
   ```

Note: Using `wget` to update individual files is not recommended as it:
- Doesn’t maintain proper version control
- May miss dependencies
- Could break file permissions
- Doesn’t track changes properly

Always use Git to update the entire application to ensure consistency.

## Usage

1. Open your web browser and navigate to:
   ```
   http://localhost
   ```

2. Upload your observation file (RINEX, SBF, XYZ, or LLH format)
   - Optionally check "Open results in new tab" to view results in a separate tab

3. View the results:
   - For RINEX/SBF files: satellite-specific sigma values
   - For XYZ/LLH files: epoch-by-epoch position accuracy values
   - Summary statistics for all components (Horizontal, Vertical, East, North, Up)
   - Process multiple files in succession, each opening in its own tab when the checkbox is selected

4. Compare two files:
   - Upload two files in the Compare tab
   - View individual statistics for each file
   - See color-coded differences between files:
     - Green: < 5% difference
     - Yellow: 5-10% difference
     - Red: > 10% difference
   - Optionally open comparison results in a new tab

5. Download a PDF report with the complete analysis

## Notes
- The application maintains the 10 most recent calculation results in memory
- When processing multiple files with "Open in new tab" selected, each file's results will open in a separate browser tab
- Results in the main page are only shown when "Open in new tab" is not selected

## Verified Files

This section lists files that have been successfully tested with the NohrTech Sigma Calculator. Each entry includes the file type and source information to help users understand the range of supported files.

### Test Results

### Verified Files

1. Emlid Reach M2 LLH File
   - File: `ZS-1289_solution_20240307085442.LLH`
   - Format: Geodetic coordinates (Lat, Lon, Height)
   - Properties:
     - Contains accurate standard deviations for E, N components
     - Up component handled with individual epoch processing
     - Results show consistent accuracy values
   - File Structure:
     ```
     GPS Time, Latitude, Longitude, Height, Q, NS, sE, sN, sU
     1234567890,   60.00,    10.00,  100.0, 1,  8, 0.010, 0.015, 0.025
     ```

2. Emlid Reach M2 XYZ File
   - File: `ZS-1289_solution_20240315113418.XYZ`
   - Format: ECEF XYZ coordinates with accuracy metrics
   - Properties:
     - Epoch-by-epoch analysis shows stable solutions
     - Consistent accuracy values across components
     - High-quality fixed solutions
   - File Structure:
     ```
     GPS Time,        X,        Y,        Z, Q, NS,   sX,   sY,   sZ
     1234567890, 3000000,  1000000,  5000000, 1,  8, 0.010, 0.015, 0.025
     ```

3. Septentrio SBF File
   - Format: Binary format containing GNSS measurements
   - Properties:
     - Successfully processes PVTGeodetic blocks
     - Variable accuracy noted in test results
     - Detailed statistics available for analysis
   - Key Blocks:
     - PVTGeodetic: Position, velocity, and time in geodetic coordinates
     - PVTCartesian: Position, velocity, and time in ECEF coordinates
     - DOP: Dilution of precision values

4. RINEX Observation File
   - Format: Standard RINEX format
   - Properties:
     - Successfully tested with files converted from Trimble T04 format
     - High-quality fixed solutions observed
     - Excellent precision in both horizontal and vertical components
   - Supported Data:
     - GPS observations
     - GLONASS observations
     - Galileo observations (where available)

### Summary of Test Results

1. **LLH Files**:
   - Reliable standard deviations for E, N components
   - Accurate vertical sigma calculation per epoch
   - Consistent results across all test files

2. **XYZ Files**:
   - Stable solutions with good precision
   - Accurate transformation to local coordinates
   - Reliable accuracy metrics

3. **SBF Files**:
   - Robust parsing of binary format
   - Accurate extraction of position and accuracy data
   - Variable accuracy depending on solution quality

4. **RINEX Files**:
   - High-quality position solutions
   - Accurate sigma calculations
   - Good performance with converted T04 files

## Output

The calculator provides the following information for each supported file type:

### RINEX/SBF Files
- Satellite-specific sigma values
- Horizontal sigma (RMS of East and North components)
- Vertical sigma (RMS of Up component value per epoch)
- Component-wise analysis (East, North, Up)

### XYZ Files
- Epoch-by-epoch position accuracy
- Horizontal sigma (RMS of East and North per epoch)
- Vertical sigma (RMS of Up component value per epoch)
- Individual East, North, Up components
- Summary statistics for all components

### Calculation Methods

#### Horizontal Sigma
The horizontal sigma is calculated for each epoch as the Root Mean Square (RMS) of the East and North components:
```
σ_H = √((σ_E² + σ_N²) / 2)
```

#### Vertical Sigma
The vertical sigma is calculated using RMS in two steps:

1. For each epoch, calculate the RMS of the Up component:
```
σ_V = √(σ_U²)
```

2. For overall vertical accuracy, calculate the RMS across all epochs:
```
σ_V_total = √(∑(σ_V²) / n)
```
where n is the number of epochs.

The source of the Up component (σ_U) depends on the file type:
- For SBF files: `sigma_up` value from PVTGeodetic blocks
- For XYZ/LLH files: sU (Up standard deviation) value from each epoch
- For RINEX files: Set to 1.5 times the nominal horizontal accuracy

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

NohrTech - Precision GNSS Solutions

# GNSS Sigma Calculator

A comprehensive Python tool for analyzing GNSS measurement uncertainties and data distributions across multiple file formats. This tool supports multiple GNSS data formats and provides detailed statistical analysis of the measurements.

## Features

- **Multi-format Support**:
  - RINEX 3.x Observation Files (*.rnx, *.obs)
  - LLH (Latitude/Longitude/Height) Files (*.llh)
  - XYZ (Cartesian Coordinates) Files (*.xyz)
  - SBF Files (*.sbf) - Future support planned

- **Analysis Capabilities**:
  - Standard deviation (sigma) calculation for each component
  - Data distribution analysis within 1σ and 2σ ranges
  - Comparison with provided uncertainty values (when available)
  - Overall position uncertainty estimation
  - Automatic unit conversion and scaling

## Usage

```bash
python nohrtech_sigma.py <input_file>
```

### Input File Types

1. **RINEX Files (*.rnx, *.obs)**:
   - Supports RINEX version 3.x
   - Focuses on GPS pseudorange measurements
   - Handles multiple observation types (C1*, P1*, C2*, P2*)
   - Accounts for epoch flags and special events

2. **LLH Files (*.llh)**:
   - Format: Timestamp Lat Lon Height Status Sats σLat σLon σHeight [additional fields]
   - Automatically converts angular uncertainties to meters
   - Accounts for latitude-dependent scaling of longitude uncertainties

3. **XYZ Files (*.xyz)**:
   - Format: Timestamp X Y Z [σX σY σZ] [additional fields]
   - Direct processing of Cartesian coordinates
   - Supports files with or without provided uncertainties

## Output

The tool provides:
- Number of valid measurements processed
- Per-component analysis (when applicable):
  - Standard deviation (sigma)
  - Mean value
  - Provided uncertainty values (if available)
  - Data distribution statistics
- Overall position uncertainty
- Distribution analysis compared to theoretical normal distribution

## Example Output

```
Results:
----------------------------------------
Number of measurements: 23569

Latitude Component:
Sigma (std dev):     0.015 meters
Mean:                60.80042570 degrees
Provided sigma:      1.113 meters
Data within 1-sigma: 99.3% (expected: 68.27%)
Data within 2-sigma: 99.9% (expected: 95.45%)

[Additional components...]

Overall position sigma: 0.029 meters
```

## Requirements

- Python 3.6 or higher
- NumPy

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install numpy
   ```

## Recent Updates

- Added support for RINEX 3.04 mixed observation files
- Improved handling of latitude/longitude uncertainty conversions
- Enhanced data distribution analysis
- Added proper scaling for pseudorange measurements
- Fixed RINEX header parsing for observation types
- Improved error handling and reporting

## Notes

- For LLH files, latitude/longitude uncertainties are converted to meters using appropriate scaling factors
- RINEX processing focuses on GPS observations for consistency
- All sigma values are reported in meters for easy comparison
- Data distribution analysis compares actual vs. theoretical normal distribution

## Future Enhancements

- Add support for SBF file format
- Implement time-series analysis
- Add graphical output options
- Support for additional GNSS constellations
- Enhanced statistical analysis tools
