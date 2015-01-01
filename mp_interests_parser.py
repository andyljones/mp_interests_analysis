# -*- coding: utf-8 -*-
"""
Created on Wed Dec 31 17:25:08 2014

@author: andyjones
"""

import json
import pandas as pd
import bs4
import re


def get_scraped_data_into_dataframe():
    """Gets the scraped data from its JSON file and formats it as a dataframe"""
    scraped_data_path = "mp_interests_scraping/mp_interests_scraped_data.json"
    scraped_data = pd.DataFrame(json.load(open(scraped_data_path)))
    scraped_data['date_string'] = scraped_data['url'].str.split('/').apply(lambda x: x[-2])
    scraped_data['mp_string'] = scraped_data['url'].str.split('/').apply(lambda x: x[-1].split('.')[0])
    
    index = pd.MultiIndex.from_arrays(scraped_data[['mp_string', 'date_string']].values.T)
    scraped_data.index = index
    scraped_data = scraped_data.drop(['date_string', 'mp_string'], axis=1)
    scraped_data = scraped_data.sort_index()
    
    scraped_data = scraped_data.query('ilevel_1 != \"100927\"')
    scraped_data['main_text'] = scraped_data['main_text'].apply(lambda x: x[0])
    
    return scraped_data
    
scraped_data = get_scraped_data_into_dataframe()


test_text = scraped_data.loc['abbott_diane', '141208']['main_text']
soup = bs4.BeautifulSoup(test_text)

class Node:
    def __init__(self, value = None):
        self.value = value
        self.children = []
        
    def __getitem__(self, i):
        return self.children[i]
        
    def __setitem__(self, i, v):
        self.children[i] = v
    
    def __repr__(self):
        return "Node(%r, %d children)" % (self.value, len(self.children))

def get_level(tag):
    if tag is "root":
        return -1
    elif list(tag.strings) and any(map(lambda s: re.match('^\s*\d+\.', s), tag.strings)):
        return 0
    elif "class" in tag.attrs and "indent" in tag["class"]:
        return 1
    elif "class" in tag.attrs and "indent2" in tag["class"]:
        return 2
    elif "class" in tag.attrs and "indent3" in tag["class"]:
        return 3
    elif list(tag.stripped_strings):
        return 4
    
def extract_relevant_tags(text):
    soup = bs4.BeautifulSoup(text)
    tags = soup.body.div.findAll(["p", "h3"], recursive=False)
    tags = [tag for tag in tags if get_level(tag) is not None]

    root = Node("root")
    current_path = [root]   
    for tag in tags:
        level = get_level(tag)
        while get_level(current_path[-1].value) >= level:
            current_path.pop()
            
        node = Node(tag)
        current_path[-1].children.append(node)
        current_path.append(node)
            
    
    return root
    
#results = scraped_data.xs("141208", level=1)['main_text'].apply(lambda x: extract_relevant_tags(x))
