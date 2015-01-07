# -*- coding: utf-8 -*-
"""
Created on Mon Jan  5 09:32:13 2015

@author: andyjones
"""

import pandas as pd
import os

data_folder = "companies_house_data/"
selected_data_path = "companies_house_selected_data.csv"

def extract_data():
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]    
    dataframes = [pd.read_csv(os.path.join(data_folder, f)) for f in csv_files]
    dataframe = pd.concat(dataframes)
    
    relevant_data = dataframe.filter(regex='.*SICCode.*|CompanyNumber|^CompanyName')

    relevant_data.to_csv(selected_data_path)
    
def load_data():
    return pd.read_csv(selected_data_path).set_index(' CompanyNumber')
    
#relevant_data = relevant_data if "relevant_data" in locals() else load_data()
