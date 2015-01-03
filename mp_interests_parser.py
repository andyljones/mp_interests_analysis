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

def is_subsection_heading(tag):
    """Tests if the given tag is the header for a subsection."""
    has_susbsection_formatting = tag.name == "h3" 
    has_subsection_text = list(tag.strings) and any(map(lambda s: re.match('^\s*\d+\.', s), tag.strings))

    return has_susbsection_formatting and has_subsection_text

def is_a_spacer(tag):
    """Tests if the given tag is a spacer"""
    return "class" in tag.attrs and "spacer" in tag["class"]

def text(tags):
    """Gets all the nonempty strings in a collection of tags, and returns them as a single string
    divided by newlines"""
    return "\n".join(list(itertools.chain(*[tag.stripped_strings for tag in tags])))

def subsections(html):
    """Returns a list of (header_tag, [contained_tag]) elements, each one representing a subsection"""
    soup = bs4.BeautifulSoup(html)
    tags = soup.body.div.findAll(True, recursive=False)

    subsections = []

    for tag in tags:
        if is_subsection_heading(tag):
            subsections.append((tag, []))
        elif subsections:
            subsections[-1][1].append(tag)
        
    return subsections
    
def group_text_by_spacer(tags):
    """Groups a list of tags according to where spacer tags appear. Discards the spacer tags themselves"""
    return [text(group) for key, group in itertools.groupby(tags, is_a_spacer) if not key]
    
def text_subsections(html):
    """Returns a list of (header_text, [contained_text]) elements, each one representing a subsection. The
    contained_text components formed by all the text lying between sequential spacer tags"""
    
    return [(text([header]), group_text_by_spacer(contents)) for header, contents in subsections(html)]

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
    
def gbp_and_named_entities(html):
    """Extracts a list of (quantity, [name]) from the given HTML. Each tuple corresponds to a spacer-deliminted
    section of the HTML"""
    
    text = list(itertools.chain(*[contents for _, contents in text_subsections(html)]))
    
    entities = [named_entities(t) for t in text]
    gbp = [sum(list_of_gbp) for list_of_gbp in [quantities_of_gbp(t) for t in text]]
    
    return zip(gbp, entities)




#results = scraped_data.xs("141208", level=1)['main_text'].apply(lambda x: tag_tree(x))
test_html = scraped_data.xs("141208", level=1)['main_text'].iloc[-1]
#test_text = list(results.iloc[0][0][0][0].value.strings)[0]
#sentences = nltk.tokenize.sent_tokenize(test_text)
#test_sentence = sentences[0]

