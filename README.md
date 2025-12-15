# RicePro - Insect Pest Management System

A comprehensive Streamlit application for managing insect pest data (Rice Black Bug and White Stem Borer) and environmental factors with CRUD operations, advanced analytics, and **Google Sheets integration**.

## Features

- **📊 Dashboard**: Overview of pest populations and environmental conditions
- **📋 Pest Records Management**: CRUD operations for pest observation data
- **🌍 Environmental Factors Management**: Track and manage environmental data
- **📈 Analytics & Insights**: Trends, correlations, and statistical analysis
- **☁️ Google Sheets Integration**: Sync data automatically with Google Sheets
- **⚙️ Data Management**: Import data from CSV files

## Dataset Information

### Pest Records Dataset
- File: `DS October 2024-March 2025_RBB Daily Light Trap Data.xlsx - Aggregated.csv`
- Contains: Daily pest counts (RBB and WSB) with environmental measurements
- Columns: Year, Month, Day, Location (Latitude/Longitude), Pest counts, Temperature, Humidity, Precipitation

### Environmental Factors Dataset
- File: `cumulative_weekly_avg_per_week_across_years_12.11.2025 (1).csv`
- Contains: Weekly environmental measurements and pest aggregations
- Columns: Year, Week Number, Solar radiation, UV indices, Temperature, Humidity, Wind speed, Precipitation

## Installation

1. Clone or navigate to the project directory:
```bash
cd c:\Users\USER\Desktop\riceprotek_app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Google Sheets Setup (Optional but Recommended)

To enable Google Sheets integration for cloud-based data storage:

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Google Sheets API** and **Google Drive API**

### Step 2: Create Service Account
1. Go to **Service Accounts** (under IAM & Admin)
2. Click **Create Service Account**
3. Fill in the details and click **Create**

### Step 3: Create and Download Key
1. In the Service Account details, go to **Keys** tab
2. Click **Add Key** → **Create new key**
3. Choose **JSON** format
4. Download the key file

### Step 4: Configure Application
1. Open `.streamlit/secrets.toml` in your project
2. Replace the placeholder with your service account JSON key contents
3. Save the file

### Step 5: Share Google Sheet
1. Open your Google Sheet: [RicePro Data Sheet](https://docs.google.com/spreadsheets/d/1Vp_EI-o9Cn8cpoUhwCR-_C3o_oIkMA0J/)
2. Click **Share**
3. Add the service account email (from the JSON key)
4. Give it **Editor** access

## Running the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## Usage

### Dashboard
- View real-time summary metrics for pest populations
- Monitor temperature, humidity, and precipitation trends
- Compare RBB vs WSB populations

### Pest Records
- **View**: Filter and explore existing pest records
- **Add**: Create new pest observation records with option to save to local database, Google Sheets, or both
- **Edit**: Modify existing records
- **Delete**: Remove records (with confirmation)

### Environmental Factors
- **View**: Browse environmental measurements
- **Add**: Record new environmental data
- **Edit**: Update existing measurements
- **Delete**: Remove records

### Analytics
- **Summary Statistics**: View distribution metrics for pest counts
- **Trends**: Analyze temporal patterns (daily, monthly, yearly)
- **Correlations**: Examine relationships between pests and environmental factors
- **Outliers**: Detect unusual values using statistical methods

### Settings
- **Load Data**: Import pest records and environmental factors from CSV
- **Database Info**: View local database statistics
- **Google Sheets**: Sync data between local database and Google Sheets

## Project Structure

```
riceprotek_app/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── secrets.toml               # Google Sheets credentials (add your key here)
├── utils/
│   ├── database.py                # SQLite database operations
│   ├── data_processing.py         # Data analysis and aggregation
│   ├── visualizations.py          # Plotly chart generation
│   └── google_sheets.py           # Google Sheets API integration
├── data/
│   └── pest_management.db         # SQLite database (created on first run)
└── README.md                       # This file
```

## Database Schema

### Local Database (SQLite)

#### pest_records table
- id, year, month, day
- latitude, longitude, cluster, area_code
- rbb_count, wsb_count
- temperature, max_temp, min_temp
- humidity, precipitation
- created_at, updated_at

#### environmental_factors table
- id, year, week_number, month, day
- moon_category
- rbb_weekly, wsb_weekly
- clear_sky_par, allsky_uva, allsky_uvb
- temp_2m, temp_2m_min, temp_2m_max
- humidity_2m, precipitation
- wind_speed_2m, wind_speed_2m_max, wind_speed_2m_min
- wind_direction, gwe_top
- created_at, updated_at

### Google Sheets
- **Pest Records Sheet**: Same columns as local database
- **Environmental Factors Sheet**: Same columns as local database
- Automatically synced with timestamps

## Technologies Used

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **SQLite3**: Local database
- **Plotly**: Interactive visualizations
- **NumPy**: Numerical computing
- **Google Sheets API**: Cloud data synchronization

## Data Saving Options

When adding new records, choose where to save:
- **Local Database**: SQLite only (fast, offline access)
- **Google Sheets**: Cloud storage only (shareable, collaborative)
- **Both**: Sync to both local and cloud (redundancy and sharing)

## Features Overview

### Dashboard
- Key performance indicators (KPIs)
- Time series charts for pest trends
- Comparative analysis between RBB and WSB

### Data Management
- Complete CRUD operations
- Multi-column filtering
- CSV export functionality
- Batch import from CSV files
- Cloud synchronization with Google Sheets

### Analytics
- Descriptive statistics
- Temporal aggregation (daily, monthly, yearly)
- Scatter plots with trend lines
- Distribution histograms
- Outlier detection using z-score

## Tips for Use

1. **Initial Setup**: Follow the Google Sheets setup section for cloud integration
2. **Data Import**: Start by loading sample datasets from Settings page
3. **Dashboard**: Use for quick overview of current pest situation
4. **Records**: Manually add new observations with choice of storage location
5. **Sync**: Use the Google Sheets tab in Settings to sync between local and cloud
6. **Export**: Download filtered data for further analysis in Excel/R/Python

## Troubleshooting

### Google Sheets Not Connecting
- Verify credentials are correctly added to `.streamlit/secrets.toml`
- Ensure the service account email is added to the shared Google Sheet
- Check that Google Sheets API is enabled in Google Cloud Console

### Data Not Syncing
- Click the "Sync Local to Google Sheets" button in Settings
- Verify sheet permissions and service account access
- Check that spreadsheet ID matches in `utils/google_sheets.py`

### CSV Import Issues
- Ensure CSV files are in the correct location
- Check that column names match expected format
- Verify file encoding (UTF-8 recommended)

## Future Enhancements

- Predictive modeling for pest population forecasting
- Multi-location comparison tools
- Weather API integration for real-time data
- Advanced statistical modeling
- Mobile responsiveness improvements
- User authentication and multi-user support
- Data export to multiple formats
- Automated alerts and notifications

## Support

For issues or questions, please contact the development team or create an issue in the repository.

## License

This project is provided as-is for agricultural research and pest management purposes.

