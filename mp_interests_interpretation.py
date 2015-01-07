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
        
        
#successes = 0
#tries = 0
#for mp, row in mp_interest_data.iterrows():
#    for entity in filter(bool, row.entities):
#        leading_np = entity[0]
#        closest_match = find_closest_company(leading_np, companies_house_lookup, companies_house_data)
#        if len(closest_match) == 1:
#            successes = successes + 1
#        
#        tries = tries + 1
