# GravityLog

## Introduction

This Streamlit application serves as a tool for tracking and managing body measurements over time. It enables users to record, visualize, and analyze weight and body composition metrics: weight along with body fat, water content, and muscle mass. _GravityLog_ is designed for individuals who want to monitor their body composition changes, whether for fitness goals, health monitoring, or weight management. While being comprehensive in its tracking capabilities, it maintains a straightforward and practical approach to data management and visualization.

**Data Visualization:**
- Chronological progress tracking
- Trend analysis with customizable time ranges
- Prediction when target weight will be reached based on current trend
- Body composition analysis (percentage or kg)

**Measurement Management:**
- Record and edit body measurements (weight in kg, body composition in %)
- Auto-fill feature based on previous measurements
- Date-based entries with update and delete capabilities
- Tabular overview of all recorded measurements

**User Management:**
- Multi-user support with individual profiles
- User profile customization (height and target weight)
- Basic user administration (add, edit, delete)
- Data persistence through CSV files

The interface aims to be straightforward and functional, focusing on providing useful information without unnecessary complexity. As the application runs entirely on your local machine, all data remains under your control and is stored locally in simple CSV files. This ensures complete data privacy while maintaining easy access to your data for backup or external analysis if desired.

## Installation

Clone this repository

```zsh
git clone https://github.com/azabicki/GravityLog
```

### virtual environment

_GravityLog_ is written in `Python 3.11.2`.

#### venv
Install a virtual environment according to your OS:

##### MacOS & Linux

```zsh
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

##### Windows

```sh
py -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Conda

If you are using _*conda_, an environment.yml file is provided, which also installs the required python version `3.11.2`:

```zsh
conda env create -f environment.yml
conda activate GravityLog
```

## Usage

To start the app, run the following command:

```zsh
streamlit run GravityLog.py
```

The app will be available at http://localhost:8501.

Using _GravityLog_ is straightforward. Simply select a user profile from the dropdown menu, and start tracking your body composition. You can also create multiple user profiles to track different persons.

## Data Privacy

This application runs entirely locally on your machine. All user data is stored in CSV files in the `data/` directory, ensuring complete control over your personal information.

## Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
