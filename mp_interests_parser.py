# -*- coding: utf-8 -*-
"""
Created on Wed Dec 31 17:25:08 2014

@author: andyjones
"""

import json
import pandas as pd
import bs4
import re
import nltk
import senna
import itertools


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
    scraped_data.loc[:, 'main_text'] = scraped_data['main_text'].apply(lambda x: x[0])
    
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
        
    def tree_str(self, level=0):
        self_string = "\t"*level + repr(self.value)
        child_string = ''.join([child.tree_str(level+1) for child in self.children])
        
        return self_string + "\n" + child_string                
    
    def __str__(self):
        return self.tree_str()

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

def quantities_of_gbp(text):
    """Looks for anything that resembles an quantity of GBP in the text of a tag, and turns them into
    a list of ints"""
    
    quantity_strings = re.findall('(?<=\xa3)[\d,]*', text)
    quantities = [int(s.replace(',', '')) for s in quantity_strings]

    return quantities
    
def named_entities(text):
    """Uses SENNA to extract the tokens corresponding to named entities in a chunk of text"""
    
    sentences = nltk.tokenize.sent_tokenize(text)    
    
    tagger = senna.SennaTagger('/Users/andyjones/senna', ['ner'])
    tagged_tokens = tagger.tag_sents(sentences)
    
    all_named_entity_phrases = []    
    
    for sentence_tokens in tagged_tokens:
        chunks = itertools.groupby(sentence_tokens, lambda x: x['ner'] == 'O')
        named_entity_chunks = [list(chunk) for k, chunk in chunks if not k]
        named_entity_phrases = [' '.join([token['word'] for token in chunk]) for chunk in named_entity_chunks]

        all_named_entity_phrases.extend(named_entity_phrases)    
    
    return all_named_entity_phrases

def non_address_named_entities(text):
    sentences = nltk.tokenize.sent_tokenize(text)    
    non_address_sentences = [s for s in sentences if not re.match("Address:", s)]
    
    return named_entities(' '.join(non_address_sentences))

def map_over_tree(root, f):
    """Applies the function f to the value of each node in the tree under the given root, 
    and stores the result in a new tree"""
    
    result = f(root.value)
    new_children = [map_over_tree(child, f) for child in root.children]

    new_root = Node(result)    
    new_root.children = new_children

    return new_root    

def map_over_text_in_tag_tree(root, f):
    """Applies the function f to the text of each tag in the tree under the given root,
    and stores the result in a new tree. Nodes which are not of bs4.element.Tag type are preserved"""

    def g(value):
        if type(value) == bs4.element.Tag:
            text = '\n'.join(value.stripped_strings)
            return f(text)
        else:
            return value
        
    return map_over_tree(root, g)
     
def merge_trees(left_root, right_root):
    """Assuming the trees have the same structure, returns a new tree with the values of each pair of nodes 
    tupled. If the trees' structure differs, raises a ValueException"""
    
    new_value = (left_root.value, right_root.value)
    
    left_size = len(left_root.children)
    right_size = len(right_root.children)
    if left_size == right_size:
        new_children = [merge_trees(*root_pair) for root_pair in zip(left_root.children, right_root.children)]
    else:
        raise ValueError("Unequal numbers of children: left root had %d but right root had %d" % (left_size, right_size))

    new_root = Node(new_value)
    new_root.children = new_children
    
    return new_root

def group_tag_text(first_tag, last_tag):
    """Groups the text of a set of tags, with the groups delineated by 
        - tags with the class 'spacer'
        - tags of different depth to the first tag"""

    first_depth = depth(first_tag)
    text_groups = [[]]
    
    current_element = first_tag 
    # Loop over the elements between the first & last tags.
    while True:
        # If the current element is of interest, use it to either add to the most recent textgroup, or to
        # start a new one.
        if type(current_element) == bs4.element.Tag:
            if "class" in current_element.attrs and "spacer" in current_element["class"]:
                text_groups.append([])
            elif "class" in current_element.attrs and depth(current_element) != first_depth:
                text_groups.append([])
            elif "class" in current_element.attrs and depth(current_element) == first_depth:
                text_groups[-1].extend(current_element.stripped_strings)
            
        if current_element == last_tag:
            break
        else:
            current_element = current_element.next_sibling

    nonempty_text_groups = [group for group in text_groups if group]
    
    return nonempty_text_groups

#results = scraped_data.xs("141208", level=1)['main_text'].apply(lambda x: tag_tree(x))
#test_text = list(results.iloc[0][0][0][0].value.strings)[0]
#sentences = nltk.tokenize.sent_tokenize(test_text)
#test_sentence = sentences[0]

