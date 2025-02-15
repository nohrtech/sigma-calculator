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
  - Vertical sigma: Direct Up component value per epoch
  - Individual epoch-by-epoch analysis for all components
  - Statistical analysis across all epochs
- Open results in a new tab for better viewing and comparison
- Process multiple files in separate tabs

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
   wget -O- https://raw.githubusercontent.com/nohrtech/sigma-calculator/main/install.sh | sudo bash
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

## Development Setup

### Setting Up Your Development Environment

1. Install Git:
   - Windows: Download and install from https://git-scm.com/download/win
   - Linux: `sudo apt-get install git`
   - macOS: `brew install git`

2. Configure Git:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

3. Create a GitHub account at https://github.com if you don't have one.

4. Create a new repository on GitHub:
   - Go to https://github.com/new
   - Name it "sigma-calculator"
   - Make it public
   - Don't initialize with README (we already have one)

5. Push your code to GitHub:
   ```bash
   # Initialize Git repository
   git init
   
   # Add all files
   git add .
   
   # Commit changes
   git commit -m "Initial commit"
   
   # Add GitHub repository as remote
   git remote add origin https://github.com/nohrtech/sigma-calculator.git
   
   # Push to GitHub
   git push -u origin main
   ```

### Repository Structure
```
sigma-calculator/
├── app.py                 # Flask web application
├── nohrtech_sigma.py      # Core sigma calculation logic
├── sbf_parser.py          # SBF file parser
├── analyze_sbf.py         # SBF analysis utilities
├── pdf_generator.py       # PDF report generation
├── install.sh            # Installation script
├── requirements.txt      # Python dependencies
├── README.md            # Documentation
├── .gitignore           # Git ignore rules
└── templates/           # HTML templates
    ├── index.html
    ├── results.html
    └── documentation.html
```

### Contributing

1. Create a new branch for each feature:
   ```bash
   git checkout -b feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

3. Push your branch to GitHub:
   ```bash
   git push origin feature-name
   ```

4. Create a Pull Request on GitHub for review.

## Deployment Notes

The application is set up to run under Apache with mod_wsgi. After installation:

- Application files are in `/var/www/sigma-calculator`
- Apache logs are in `/var/log/apache2/sigma-calculator-{error,access}.log`
- To update the application:
  ```bash
  cd /var/www/sigma-calculator
  sudo git pull
  sudo systemctl restart apache2
  ```

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

4. Download a PDF report with the complete analysis

## Notes
- The application maintains the 10 most recent calculation results in memory
- When processing multiple files with "Open in new tab" selected, each file's results will open in a separate browser tab
- Results in the main page are only shown when "Open in new tab" is not selected

## Verified Files

This section lists files that have been successfully tested with the NohrTech Sigma Calculator. Each entry includes the file type and source information to help users understand the range of supported files.

### RINEX Files

1. `IGS000USA_R_20250461031_06H_30S_MO.rnx`
   - Source: Trimble R750 GNSS receiver
   - Format: RINEX 3.x Mixed Observation file
   - File Properties:
     - Station: IGS000USA
     - Year: 2025, Day of Year: 046 (Feb 15)
     - Start Time: 10:31
     - Duration: 6 Hours
     - Sample Rate: 30 Seconds
     - Type: Mixed Observation (MO)
   - Solution Quality:
     - Very stable fixed solution
     - Consistent accuracy values:
       - East: 10mm
       - North: 10mm
       - Up: 15mm
     - Horizontal RMS: 10mm
   - Processing Status: Successfully processed
   - Notes: 
     - Converted from Trimble T04 format to RINEX
     - Shows excellent precision typical of a high-quality fixed RTK solution
     - Vertical accuracy ratio to horizontal (1.5x) is within expected range
     - No significant variations in accuracy values throughout the session

### SBF Files

1. `log__000.sbf`
   - Source: Septentrio GNSS receiver
   - Format: Septentrio Binary Format (SBF)
   - File Structure:
     - Binary format with sync markers and block IDs
     - Contains PVTGeodetic blocks (ID: 0x0fa2) with position and accuracy data
     - Other blocks include satellite tracking and receiver status
   - Recording Duration: ~40 minutes
   - Data Content:
     - GPS Week: 2353
     - Position data in geodetic coordinates (lat, lon, height)
     - Accuracy metrics for horizontal and vertical components
   - Solution Quality:
     - Variable solution quality with significant accuracy changes
     - Accuracy ranges:
       - Horizontal: 35-127mm (typical), up to 178mm in some epochs
       - Vertical: 50-179mm
     - Mean accuracies:
       - Horizontal: 89mm
       - Vertical: 98mm
   - Processing Status: Successfully processed
   - Notes: 
     - File shows transitions between different solution qualities
     - Accuracy values indicate RTK float or DGPS solutions
     - Some epochs show very high accuracy (35mm), while others show reduced precision
     - Standard deviations indicate significant variation in solution quality

### Emlid XYZ Files

1. `ZS-1289_solution_20240315113418.XYZ`
   - Source: Emlid Reach M2 GNSS receiver
   - Format: ECEF XYZ coordinates with accuracy metrics
   - File Structure:
     ```
     Time X Y Z Q NS sE sN sU dE dN dU AGE AR
     ```
     Where:
     - Time: YYYY/MM/DD HH:MM:SS.FFF format
     - X, Y, Z: ECEF coordinates in meters
     - Q: Solution quality indicator
     - NS: Number of satellites
     - sE, sN, sU: Standard deviations in meters for East, North, Up
     - dE, dN, dU: Position deltas in meters
     - AGE: Age of corrections in seconds
     - AR: Ambiguity resolution status
   - Sampling Rate: 5 Hz (0.2 second intervals)
   - Duration: ~22 minutes
   - Solution Quality:
     - Fixed solution with good satellite coverage
     - Consistent accuracy values:
       - East: 4.7-5.7mm
       - North: 9.1-9.3mm
       - Up: 13.6-15.4mm
   - Processing Status: Successfully processed
   - Notes: 
     - File includes comprehensive positioning data
     - Standard deviations are provided directly in meters
     - Very stable solution with millimeter-level precision

### Emlid LLH Files

1. `ZS-1289_solution_20240307085442.LLH`
   - Source: Emlid Reach M2 GNSS receiver
   - Format: Latitude/Longitude/Height with accuracy metrics
   - File Structure:
     ```
     Time LAT LON HEIGHT Q NS sE sN sU dE dN dU AGE AR
     ```
     Where:
     - Time: YYYY/MM/DD HH:MM:SS.FFF format
     - LAT, LON: Position in decimal degrees
     - HEIGHT: Ellipsoidal height in meters
     - Q: Solution quality indicator
     - NS: Number of satellites
     - sE, sN, sU: Standard deviations in meters for East, North, Up
     - dE, dN, dU: Position deltas in meters
     - AGE: Age of corrections in seconds
     - AR: Ambiguity resolution status
   - Sampling Rate: 5 Hz (0.2 second intervals)
   - Duration: ~1.5 hours
   - Solution Quality:
     - Fixed solution with 19-22 satellites
     - Consistent accuracy values:
       - East: 10mm (0.01m)
       - North: 10mm (0.01m)
       - Up: 11mm (0.011m)
   - Processing Status: Successfully processed
   - Notes: 
     - File includes comprehensive positioning data
     - Standard deviations are provided directly in meters
     - Vertical accuracy is consistently reported as 11mm

## Output

The calculator provides the following information for each supported file type:

### RINEX/SBF Files
- Satellite-specific sigma values
- Horizontal sigma (RMS of East and North components)
- Vertical sigma (Direct Up component value per epoch)
- Component-wise analysis (East, North, Up)

### XYZ Files
- Epoch-by-epoch position accuracy
- Horizontal sigma (RMS of East and North per epoch)
- Vertical sigma (Direct Up component value per epoch)
- Individual East, North, Up components
- Summary statistics for all components

### Calculation Methods

#### Horizontal Sigma
The horizontal sigma is calculated for each epoch as the Root Mean Square (RMS) of the East and North components:
```
σ_H = √((σ_E² + σ_N²) / 2)
```

#### Vertical Sigma
The vertical sigma is calculated as the direct Up component value per epoch.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

NohrTech - Precision GNSS Solutions
