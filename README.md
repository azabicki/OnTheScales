# GravityLog


## Installation virtual environment

_GravityLog_ is developed under `Python 3.11.2`.

### venv
Install the virtual environment according to your OS:

#### MacOS & Linux

```zsh
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Windows

```sh
py -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Conda

If you are using _*conda_, an environment.yml file is provided:

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

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
