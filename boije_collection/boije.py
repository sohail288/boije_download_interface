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


def main():
    boije_folder = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
