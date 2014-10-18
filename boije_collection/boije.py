# -*- coding: utf-8 -*-
import os, sys, time, json
import requests
import unicodedata
import string

from bs4 import BeautifulSoup as BSoup

#Directory Info
#Change these for your system
BOIJE_SITE_INDEX_URL = 'http://biblioteket.statensmusikverk.se/ebibliotek/boije/indexeng.htm'
DESTINATION_DIRECTORY = '/Users/Sohail/Desktop/sheet_music/'
BOIJE_DIRECTORY_NAME = 'boije_collection'


def boijeLink(letter):
    return "http://biblioteket.statensmusikverk.se/ebibliotek/boije/Boije_%c.htm"%(letter)

def getOrCreateComposerFolder(boije_folder, composer):
    path_to_create = os.path.join(boije_folder, composer)
    if not os.path.exists(path_to_create):
        os.makedirs(path_to_create)
    return path_to_create    

def getScorePDF(score_url):
    preappend_path = BOIJE_SITE_INDEX_URL[0:-12]
    pdf_url = preappend_path + score_url
    r = requests.get(pdf_url) 
    return r

def saveScorePDF(downloaded_score, score_name, composer_folder):
    content = downloaded_score.content
    file_path = os.path.join(composer_folder, "%s.pdf"%score_name)
    with open(file_path, 'w') as f:
        f.write(content)
    return (True, file_path)

def downloadAndSaveScore(boije_folder, composer, score, score_attributes):
    composer_folder = getOrCreateComposerFolder(boije_folder, composer)
    html = score_attributes[0]
    try:
        #json file indicates that this already exists
        if score_attributes[2]:
            raise Exception
        r = getScorePDF(html)
        saveScorePDF(r, score, composer_folder)
        return True
    except:
        return False

def getOrCreateBoijeFolder(destination_directory, boije_directory):
    
    path_to_create = os.path.join(destination_directory, boije_directory)
    
    if not os.path.exists(path_to_create):
        os.makedirs(path_to_create)
    return path_to_create
    
def getIndexSoup(boijelink):
    r = requests.get(boijelink)
    soup = BSoup(r.content)
    return soup

def createJsonFile(json_file_name, boije_directory_name):
    json_file_path = os.path.join(boije_directory_name, json_file_name)
    if not os.path.exists(json_file_path):
        create_json_file = open(json_file_path, 'w')
        create_json_file.close()
        return json_file_path
    return 0


def convertComposerName(composer_name):
    composer_name = u'%s'%(composer_name)
    composer_name = composer_name.translate(dict((ord(char), None) for char in ',.'))
    composer_name = composer_name.split()
    composer_name = '_'.join(composer_name)
    if not composer_name.strip():
        composer_name = 'anon'
    return composer_name

def convertScoreName(score_name):
    score_name = unicode(score_name, 'utf-8')
    score_name = ''.join([i for i in unicodedata.normalize('NFKD', score_name) if ord(i) < 128])
    score_name = score_name.split('.')
    score_name_to_return = ''
    #hackish way of testing for multiple spaces
    space_flag = False
    for split_word in score_name:
        for char in split_word:
            if char.isalnum():
                score_name_to_return += char
                space_flag = False
            elif char in string.punctuation:
                score_name_to_return += '_'
            elif char in ' ':
                if not space_flag and score_name_to_return[-1] != '_':
                    score_name_to_return += '_'
                    #finds a space character, sets flag
                    #next time around, it would have to visit the other elif loops
                    space_flag = True
        
            else:
                score_name_to_return += char
        if score_name_to_return[-1] != '_':
            score_name_to_return += '_'
    #delete the last hyphen and return
    while score_name_to_return[-1] == '_':
        score_name_to_return = score_name_to_return[:-1]
    #last check for an extra hyphen in the beginning
    if score_name_to_return[0] == '_':
        score_name_to_return = score_name_to_return[1:]
    return score_name_to_return


def convertIndexToDictionary(soup):
    #final dictionary will be {composer:{score1:(html, boije_number, downloaded) 
    dictionary_of_composers_and_their_pieces = {}
    table = soup.table
    rows = table.find_all('tr')
    for row in rows:
        list_of_row_components = []
        for column in row.find_all('td'):
            list_of_row_components.append(column.contents[0])
        #composer is the first element, followed by piece/html of file, last is boije_number
        #BeautifulSoup text is unicode, my other function can't decode unicode, so let's encode it here.
        composer = convertComposerName(list_of_row_components[0])
        score = convertScoreName(list_of_row_components[1].text.encode('utf-8'))
        score_html = list_of_row_components[1].get('href')
        #boije number appears "Boije X", so all you have to do is split it and get the last element
        boije_number = list_of_row_components[2].split()[-1]
        #I'm assuming this function will run to initialize the data, so nothing should be downloaded
        downloaded = False
        #sometimes a composers name is mispelled.  I don't have time to figure out how to remove duplicates
        #that is why, the following code checks to see if a composer already has his dictionary of scores
        #if he doesn't, a new dictionary will be associated with the composer.
        if not dictionary_of_composers_and_their_pieces.get(composer):
            dictionary_of_composers_and_their_pieces[composer] = {}
        score_dict = {score: [score_html, boije_number, downloaded]}
        dictionary_of_composers_and_their_pieces[composer].update(score_dict)
    return dictionary_of_composers_and_their_pieces

def convertIndexToJson(index_dictionary, json_file_path):
    if not os.path.exists(json_file_path) or os.path.getsize(json_file_path) > 0:
        return 0
    with open(json_file_path, 'w') as fp:
        json.dump(index_dictionary, fp, sort_keys = True, indent = 4)
    return 1 

def convertJsonToDict(json_file_path):
    if not os.path.exists(json_file_path):
        return 0
    with open(json_file_path, 'r') as fp:
        index_dictionary = json.load(fp)
    return index_dictionary

def updateJsonFile(index_dictionary, json_file_path):
    with open(json_file_path, 'w') as fp:
        json.dump(index_dictionary, fp, sort_keys = True, indent = 4)
    return 1

def main():
    boije_folder = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
