import os, sys
import requests

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

def getOrCreateBoijeFolder(destination_directory, boije_directory):
    
    path_to_create = os.path.join(destination_directory, boije_directory)
    
    if not os.path.exists(path_to_create):
        os.makedirs(path_to_create)
    return path_to_create
    
def getIndexSoup(boijelink):
    r = requests.get(boijelink)
    soup = BSoup(r.content)
    return soup

def convertIndexToDictionary(soup):
    dictionary_of_composers_and_their_pieces = {}
    table = soup.table
    rows = table.find_all('tr')
    for row in rows:
        list_of_row_components = []
        for column in row.find_all('td'):
            list_of_row_components.append(column.contents[0])
        #composer is the first element, followed by piece/html of file, last is boije_number
        composer = list_of_row_components[0]
        #manipulate composer by stripping off all parts
        #first check to see if composer field is blank
        composer = composer.translate(dict((ord(char), None) for char in ',.'))
        composer = composer.split()
        composer = '_'.join(composer)
        if not composer.strip():
            composer = 'anon'
        #next we have this composers scores
        if dictionary_of_composers_and_their_pieces.get(composer):
            dictionary_of_composers_and_their_pieces[composer] += list_of_row_components[1]
        else:
            dictionary_of_composers_and_their_pieces[composer] = []
            dictionary_of_composers_and_their_pieces[composer] += list_of_row_components[1]
    return dictionary_of_composers_and_their_pieces

def main():
    boije_folder = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
