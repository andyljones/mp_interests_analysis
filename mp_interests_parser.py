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

    # Pulls out the parts of the URL that describe the date the data was added and the MP it corresponds to
    scraped_data['date_string'] = scraped_data['url'].str.split('/').apply(lambda x: x[-2])
    scraped_data['mp_string'] = scraped_data['url'].str.split('/').apply(lambda x: x[-1].split('.')[0])
    
    # Uses the MP and date that we just extracted to construct a multi-index
    index = pd.MultiIndex.from_arrays(scraped_data[['mp_string', 'date_string']].values.T)
    scraped_data.index = index
    scraped_data = scraped_data.sort_index()
    scraped_data = scraped_data.drop(['date_string', 'mp_string'], axis=1)

    # Removes the 27/9/2010 data, which is in a different format to the rest.
    #TODO: Find a way to parse this data
    scraped_data = scraped_data.query('ilevel_1 != \"100927\"')
    
    # Gets the first (and only) element of the main_text elements in each row
    scraped_data['main_text'] = scraped_data['main_text'].apply(lambda x: x[0])
    
    return scraped_data
    
scraped_data = get_scraped_data_into_dataframe()

class Node:
    """A simple class for representing trees of values. No idea why Python doesn't already have one"""
    def __init__(self, value = None):
        self.value = value
        self.children = []
        
    def __getitem__(self, i):
        return self.children[i]
        
    def __setitem__(self, i, v):
        self.children[i] = v
    
    def __repr__(self):
        return "Node(%r, %d children)" % (self.value, len(self.children))

def depth(tag):
    """On each MP's page in the register of interests, the formatting of the tags implies a hierarchy.
    This function evaluates the depth of a tag in that hierarchy. A tag with no identifiable depth will
    return None."""
    
    if tag is "root":
        return 0
    # Tests if the tag is one of the headers, with the form "2. Some Text" or similar.
    elif list(tag.strings) and any(map(lambda s: re.match('^\s*\d+\.', s), tag.strings)):
        return 1
    elif "class" in tag.attrs and "indent" in tag["class"]:
        return 2
    elif "class" in tag.attrs and "indent2" in tag["class"]:
        return 3
    elif "class" in tag.attrs and "indent3" in tag["class"]:
        return 4
    elif list(tag.stripped_strings):
        return 5
    
def tag_tree(text):
    """On each MP's page in the register of interests, the formatting of the tags implies a hierarchy.
    This function tries to structure the tags of interest as a tree of Nodes."""
    
    soup = bs4.BeautifulSoup(text)
    
    # Extracts the tags of interest, using the depth function to decide whether the tag will actually
    # have a place in the hierarchy.    
    tags = soup.body.div.findAll(["p", "h3"], recursive=False)
    tags = [tag for tag in tags if depth(tag) is not None]

    # The dummy value "root" is used to indicate to the depth function that this is the root of the tree
    root = Node("root")
    # Gives the path from the root of the tree to the tag currently being assessed
    current_path = [root]  
    
    # Iterates over the tags, using the depth function to build them into a tree. The parent of a node is
    # the most recent node with a lower depth.
    for tag in tags:
        level = depth(tag)
        
        # Finds the most recent node with a lower depth by walking up the path to the root
        while depth(current_path[-1].value) >= level:
            current_path.pop()
            
        # Attaches the current tag to the end of the current path
        node = Node(tag)
        current_path[-1].children.append(node)
        current_path.append(node)
    
    return root
    
#results = scraped_data.xs("141208", level=1)['main_text'].apply(lambda x: tag_tree(x))
