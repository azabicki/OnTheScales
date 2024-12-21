#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $SCRIPT_DIR/../..
#echo "i am here now:"
#pwd
source .venv/bin/activate
streamlit run GravityLog.py

