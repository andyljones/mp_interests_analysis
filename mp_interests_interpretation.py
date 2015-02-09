# -*- coding: utf-8 -*-
"""
Created on Sun Jan  4 09:30:19 2015

@author: andyjones
"""

import pandas as pd
import re
import itertools
import numpy
import companies_house_parser
import string
import numpy as np
import pickle

def standardize(phrase):
    """
    Convert a phrase to a standardized format:
      - Upper case
      - Punctuation replaced with spaces
      - Collapsed whitespace
      - Stop words such as "LIMITED", "LTD", "LLC", "PLC" removed
    """
    punc_re = re.compile('[%s]' % re.escape(string.punctuation))
    punc_free_phrase = punc_re.sub(' ', phrase)
    standardized_phrase = punc_free_phrase.upper()
    
    stop_words = set(["LIMITED", "LTD", "LLC", "PLC"])
    words = [w for w in standardized_phrase.split(' ') if w and w not in stop_words]

    return ' '.join(words)

def word_prefixes(phrase):
    """Returns a list of the space-seprated prefixes of a phrase"""
    words = standardize(phrase).split(' ')
    heads = [' '.join(words[:l]) for l in range(1, len(words) + 1)]
    
    return heads
    
def build_lookup(numbers_and_names):
    """Constructs a lookup table that associates each prefix of company names in the given table with a 
    list of corresponding company numbers"""
    lookup = {}
    for i, (key, name) in enumerate(numbers_and_names.iteritems()):
        for prefix in word_prefixes(name):
            if prefix in lookup:
                lookup[prefix].append(key)
            else:
                lookup[prefix] = [key]
                
        if i%100000 == 0: print('Iteration {0}'.format(i))                
                
    return lookup
    
def find_closest_company(name, lookup):
    """Returns a list of the numbers of the companies with names that share the longest prefix
    with the given name"""
    prefixes = word_prefixes(name)

    best_matches = []  
    for prefix in prefixes:
        best_matches = lookup.get(prefix, best_matches)
        
    return best_matches

mp_interest_data = pd.read_pickle("141208_parsed_interests.pickle")
companies_house_data = companies_house_data if "companies_house_data" in locals() else companies_house_parser.load_data()
companies_house_lookup = companies_house_lookup if "companies_house_lookup" in locals() else build_lookup(companies_house_data.CompanyName)
        
        
def process_interest_data():
    results = pd.DataFrame(columns=['key', 'matches'], dtype=object)
    for i, (_, row) in enumerate(mp_interest_data.iterrows()):
        orgs = [e for e in row.entities if e['type'] == 'ORG']
    
        if orgs and orgs[0]['phrase'] != 'Electoral Commission':
            leading_org = orgs[0]['phrase']
            closest_matches = find_closest_company(leading_org, companies_house_lookup)
    
            closest_names = [companies_house_data.CompanyName[n] for n in closest_matches]
            
            results.loc[i, 'key'] = leading_org
            results.loc[i, 'matches'] = closest_names

    return results
