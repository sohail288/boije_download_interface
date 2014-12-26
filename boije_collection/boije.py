# -*- coding: utf-8 -*-
import os
import sys 
import shutil
import time 
import json
import copy 
import logging
import atexit
import string
import unicodedata
import getopt

import requests

from bs4 import BeautifulSoup as BSoup

# Directory Info
# Change these for your system
BOIJE_SITE_INDEX_URL = 'http://biblioteket.statensmusikverk.se/ebibliotek/boije/indexeng.htm'
DESTINATION_DIRECTORY = '/Users/Sohail/Desktop/sheet_music/'
BOIJE_DIRECTORY_NAME = 'boije_collection'
JSON_FILE_NAME = 'boije_collection.json'
BOIJE_DIRECTORY = os.path.join(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)

def usage():
    print '{:*^30}'.format("Boije Collection Downloading Interface")
    print "Usage: boije.py [options]"
    print "Options are:"
    print "\t\t -r --rename\t [rename existing boije collection scores in boije directory]"
    print "\t\t -d --download\t [download all files from boije collection database]"
    print "\t\t -s 'directory_path'  -set-directory ='directory_path'"
    print "\t\t -h --help\t [display this message]"
    return 0

def getCommandLineArgs(args):
    """ Parse command line args.  Return dictionary of key values"""
    args_dict = {
            "rename" : False,
            "download" : False,
            "directory" : None,
    }
    try:
        opts, args = getopt.getopt(args,"rds:h", ["rename", "download",
                                                    "set-directory=", "help"])

    except getopt.GetoptError as error:
        print str(error)
        usage()
        sys.exit(2)
    # parse opts, args to set dictionary values
    for o, a in opts:
        if o in ('-h', 'help'):
            # rename
            usage()
            sys.exit(1)
        elif o in ('-r', '--rename'):
            args_dict['rename'] = True
        elif o in ('-d', '--download'):
            args_dict['download'] = True
        elif o in ('-s', '--set-directory'):
            args_dict['directory'] = a          
        else:
            print "command:\t%s not recognized" % o
            usage()
            
    
    return args_dict 

def boijeLink(letter):
    """Process index character or string and return it."""
    if len(letter) == 1:
        return "http://biblioteket.statensmusikverk.se/ebibliotek/boije/Boije_%c.htm"%(letter)
    return "http://biblioteket.statensmusikverk.se/ebibliotek/boije/%s"%(letter)

def getBoijeLetterIndices():
    """Process Boije Index and return list of indices."""
    r = requests.get(BOIJE_SITE_INDEX_URL)
    soup = BSoup(r.content)
    #index links start after the first three html links on page
    index_links_tags = soup.find_all('a')[3:]
    index_links = [i.get('href') for i in index_links_tags]
    return index_links

def getUserDesktop():
    # First get user home
    user_home_path = os.path.expanduser('~')
    user_desktop_path = os.path.join(user_home_path, "Desktop")
   
    if not os.path.exists(user_desktop_path):
        os.makedirs(user_desktop_path)
     
    return user_desktop_path

def getOrCreateComposerFolder(boije_folder, composer):
    """Take composer name and boije_folder name, return path to composer"""
    path_to_create = os.path.join(boije_folder, composer)
    if not os.path.exists(path_to_create):
        os.makedirs(path_to_create)
    return path_to_create    

def getScorePDF(score_url):
    """Process score url and return binary of pdf"""
    preappend_path = BOIJE_SITE_INDEX_URL[0:-12]
    pdf_url = preappend_path + score_url
    r = requests.get(pdf_url) 
    return r

def saveScorePDF(downloaded_score, score_name, composer_folder):
    """Take binary of pdf and save it. Return a tuple(True, file_path """
    content = downloaded_score.content
    file_path = os.path.join(composer_folder, "%s.pdf"%score_name)
    with open(file_path, 'w') as f:
        f.write(content)
    return (True, file_path)

def getScorePath(composer, score_name, boije_directory=BOIJE_DIRECTORY):
    """Check to see if a score exists, return a boolean value"""
    composer_folder_path = os.path.join(boije_directory, composer)    
    score_name = '%s.pdf'%score_name
    return os.path.exists(os.path.join(composer_folder_path, score_name))

def downloadAndSaveScore(boije_folder, composer, score, score_attributes):
    """ Combine functions to download a score.  Return boolean for status"""
    composer_folder = getOrCreateComposerFolder(boije_folder, composer)
    html = score_attributes[0]
    try:
        #json file indicates that this already exists
        if (score_attributes[2] or 
                getScorePath(composer, score, boije_folder)):
            raise Exception
        print "downloading %s"%score
        r = getScorePDF(html)
        saveScorePDF(r, score, composer_folder)
        return True
    except KeyboardInterrupt:
        logging.exception('User Interupted Downloading Sequence')
        raise        
    except Exception:
        return True 
    except:
        return False

def getOrCreateBoijeFolder(destination_directory, boije_directory):
    """Create main boije folder if it doesn't exist already. return path""" 
    path_to_create = os.path.join(destination_directory, boije_directory)
    if not os.path.exists(path_to_create):
        os.makedirs(path_to_create)
    return path_to_create
    
def getIndexSoup(boijelink):
    """Return beautifulsoup of index. Input main link."""
    r = requests.get(boijelink)
    soup = BSoup(r.content)
    return soup

def createJsonFile(json_file_name, boije_directory_name):
    """Return json file path or Null depending on if json does not exist."""
    json_file_path = os.path.join(boije_directory_name, json_file_name)
    if not os.path.exists(json_file_path):
        create_json_file = open(json_file_path, 'w')
        create_json_file.close()
        return json_file_path
    return 0


def convertComposerName(composer_name):
    """Convert composer name to make it safe for file naming. Return name"""
    composer_name = u'%s'%(composer_name)
    composer_name = composer_name.translate(
        dict((ord(char), None) for char in ',.'))
    composer_name = composer_name.split()
    composer_name = '_'.join(composer_name)
    if not composer_name.strip():
        composer_name = 'anon'
    return composer_name

def convertScoreName(score_name):
    """Make score name ascii safe and return it."""
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
                    # Finds a space character, sets flag
                    # next time around, it would have to visit the 
                    # other elif loops.
                    space_flag = True
        
            else:
                score_name_to_return += char
        if score_name_to_return[-1] != '_':
            score_name_to_return += '_'
    #delete trailing hyphens
    while score_name_to_return[-1] == '_':
        score_name_to_return = score_name_to_return[:-1]
    #last check for an extra hyphen in the beginning
    if score_name_to_return[0] == '_':
        score_name_to_return = score_name_to_return[1:]
    return score_name_to_return

def consolidateIndicesToDictionary(html_list):
    """Return a dictionary in format {compser{piece:[attributes], ..}}"""
    dictionary_of_composers_and_their_pieces = {}
    for htm in html_list:
        link_to_check = boijeLink(htm)
        soup = getIndexSoup(link_to_check)
        index_dict = convertIndexToDictionary(soup)
        dictionary_of_composers_and_their_pieces.update(index_dict)
    return dictionary_of_composers_and_their_pieces

def convertIndexToDictionary(soup):
    """Takes in soup of index. Returns a dictionary of composers and pieces
    
    The dictionary has format (composer:{score:[],score2:[],..} 
                                composer2:{}..}
    """
    dictionary_of_composers_and_their_pieces = {}
    table = soup.table
    rows = table.find_all('tr')
    for row in rows:
        list_of_row_components = []
        for column in row.find_all('td'):
            list_of_row_components.append(column.contents[0])
        # Composer is the first element, followed by piece/html of file, 
        # last is boije_number.
        composer = convertComposerName(list_of_row_components[0])
        try:
            score = list_of_row_components[1]
            # BeautifulSoup text is unicode, my other function can't decode 
            # unicode, so let's encode it here.
            score = score.text.encode('utf-8')
            score = convertScoreName(score)
            score_html = list_of_row_components[1].get('href')
            # Boije number appears "Boije X", so all you have to do is split 
            # it and get the last element.
            boije_number = list_of_row_components[2].split()[-1]
        except AttributeError:
            logging.error('error:%s'%(sys.exc_info()[0]))
            #I only know of two pieces that fail.
            score = list_of_row_components[0]
            score = score.text.encode('utf-8')
            score = convertScoreName(score)
            score_html = list_of_row_components[0].get('href')
            composer = 'anon'
            boije_number = list_of_row_components[1].split()[-1]
        except:
            list_str_rep = ','.join(
                [unicode(i) for i in list_of_row_components]
                )
            logging.error('error:%s'%(sys.exc_info()[0]))
            break
        # I'm assuming this function will run to initialize the data, so 
        # nothing should be downloaded.
        downloaded = False
        # Sometimes a composers name is mispelled.  
        # Need to figure out how to remove duplicates
        # The following code checks to see if a composer already 
        # has his dictionary of scores
        # if he doesn't, a new dictionary will be associated with the composer.
        if not dictionary_of_composers_and_their_pieces.get(composer):
            dictionary_of_composers_and_their_pieces[composer] = {}
        score_dict = {score: [score_html, boije_number, downloaded]}
        dictionary_of_composers_and_their_pieces[composer].update(score_dict)
    return dictionary_of_composers_and_their_pieces


def convertIndexToJson(index_dictionary, json_file_path):
    """ Return value 0 if json_file doesnt exist or has data. Else Return 1 """
    if (not os.path.exists(json_file_path) or 
            os.path.getsize(json_file_path) > 0):
        return 0
    with open(json_file_path, 'w') as fp:
        json.dump(index_dictionary, fp, sort_keys = True, indent = 4)
    return 1 

def convertJsonToDict(json_file_path):
    """Read json file and return dictionary of composers. Else return 0"""
    if not os.path.exists(json_file_path):
        return 0
    with open(json_file_path, 'r') as fp:
        index_dictionary = json.load(fp)
    return index_dictionary

def updateJsonFile(index_dictionary, json_file_path):
    """Update Json file and return 1"""
    with open(json_file_path, 'w') as fp:
        json.dump(index_dictionary, fp, sort_keys = True, indent = 4)
    return 1

def boijeCollectionInit(destination_directory, boije_directory_name):
    """Return paths as (boije_directory, json_file)"""
    boije_directory = getOrCreateBoijeFolder(destination_directory, 
                                            boije_directory_name)
    json_file = createJsonFile(JSON_FILE_NAME, boije_directory)
    if not json_file:
        json_file = os.path.join(boije_directory, JSON_FILE_NAME)
    return boije_directory, json_file

def dictionaryInit(json_file_path):
    """If json file exists read it & return dictionary. Else return dict"""
    if (os.path.exists(json_file_path) and 
                            os.path.getsize(json_file_path) > 0):
        try:
            dictionary_of_composers = convertJsonToDict(json_file_path)
            return dictionary_of_composers
        except ValueError:
            pass
        
    indices = getBoijeLetterIndices()
    dictionary_of_composers = consolidateIndicesToDictionary(indices)
    return dictionary_of_composers

def scoreDownloader(score_dict, boije_directory, json_file_path):
    """Download scores and return dictionary at end
    
    Handles keyboard exceptions by writing currently downloaded scores to json
    file.
    Register updateJsonFile atexit to prevent repeat work.
    """
    copy_score_dict = copy.deepcopy(score_dict)
    json_update_period = 5 
    counter = 0
    ## nested dictionary
    for composer in copy_score_dict:
        current_composer = composer
        for score in copy_score_dict[composer]:
            print "checking %s"%score

            # this is experimental, not tested
            atexit.register(updateJsonFile, copy_score_dict, json_file_path)

            current_score = score
            current_score_attributes = copy_score_dict[composer][score]
            # Test to see if the score has already been downloaded
            try:
                downloaded = downloadAndSaveScore(boije_directory, composer, 
                                                 current_score, 
                                                 current_score_attributes
                                                 )
            except KeyboardInterrupt:
                updateJsonFile(copy_score_dict, json_file_path)
                sys.exit(1)
            copy_score_dict[composer][score][2] = downloaded
            
            # lets save json file after every  5 score_downloaded, 
            # highly inefficient, but should work for now.
            counter += 1

            if counter%5 == 0:
                updateJsonFile(copy_score_dict, json_file_path)
    updateJsonFile(copy_score_dict, json_file_path)
    logging.info('%d scores have been downloaded'%(counter))    
    return copy_score_dict




def loggingInit(boije_directory):
    """Return logging file name and logging file path.  Intialize loggers"""
    logging_file_name = 'boije_collection.log'
    logging_file = os.path.join(boije_directory, logging_file_name)
    logging_level = logging.DEBUG
    logging.basicConfig(filename=logging_file, 
                        level = logging_level,
                        format = "%(asctime)s:%(levelname)s:\t%(message)s",
                        datefmt = "%m/%d/%Y %H:%M %p",
                        )
    return (logging_file_name, logging_file)

def getBoijeNumber(boije_file_name):
    """ Return a string number. input will be  a string: "Boije 4.pdf" """
    split_boije_file_name_at_period = boije_file_name.split(".")
    boije_number_string = split_boije_file_name_at_period[0]
    boije_number = boije_number_string.split()[-1]
    return boije_number



def getScoreNameWithBoijeNumber(score_dictionary, boije_number):
    """ Return (composer, score). Input score_dictionary, boije number. 
        Return (None, None) if no matches found. 
    """
        
    for composer in score_dictionary: 
        for score in score_dictionary[composer]:
            current_score = score_dictionary.get(composer).get(score)
            if current_score[1] == boije_number:
                return (composer, score)
    
    return (None, None)


def renameBoijeFiles(boije_directory, json_file_path):
    """ Converts existing scores in boije folder to correct file names,
        and puts them in correct place
    """
    
    scores_dictionary = dictionaryInit(json_file_path)
 
    # start looking at all files in directory
    for rootdir, subdirs, files in os.walk(boije_directory):
        
    # break up file name if it has Boije in it
        for single_file in files:
    # if a filename is broken up it should have the format
    # ['Boije', 'N', '.pdf']
            if "Boije" in single_file:
                current_boije_number = getBoijeNumber(single_file)
                # Pass N and score_dictionary into convertBoijeFileName
                (composer, score_name) = getScoreNameWithBoijeNumber(scores_dictionary,
                                                                    current_boije_number)
                # check return
                if composer and score_name:
                    score_exists = getScorePath(composer, score_name, boije_directory)
                # CHECK TO MAKE SURE THE FILE ISN"T ALREADY THERE
                    if not score_exists:
                        composer_folder = getOrCreateComposerFolder(boije_directory, composer)
                        # scoredictionary.get(composer), score_attributes = composer.get(score)
                        score_attributes = scores_dictionary.get(composer).get(score_name)
                        # stage is now set to rename pdf 
                        # best to copy file to new name and correct directory and delete org
                        original_file = os.path.join(rootdir, single_file)
                        new_file = os.path.join(composer_folder, "%s.pdf"%score_name)
                        shutil.copy(original_file, new_file)
                        os.remove(original_file)
                        scores_dictionary[composer][score_name][2] = True
    # GetOrCreateComposerFolder, rename PDF, move it to composer folder
    # Mark True in scores dictionary
    # update jsonFileAtEnd

    updateJsonFile(scores_dictionary, json_file_path)
    # return to exit



def main():
    print "*******STARTING BOIJE COLLECTION COLLECTOR***************"

    args_dictionary = getCommandLineArgs(sys.argv[1:])
    if args_dictionary.get('directory', 0):
        destination_directory = args_dictionary['directory']
    else:
        destination_directory = getUserDesktop() 
        #download scores
    
    
    print destination_directory
    boije_directory, json_file_path = boijeCollectionInit(destination_directory,
                                                         BOIJE_DIRECTORY_NAME)
    print "setting logging file"
    logging_file_name, logging_file = loggingInit(boije_directory)
    logging.info('Started Boije Project')
    print "initializing dictionary"

    if args_dictionary.get('rename', 0):
        print "\t\tStarting Renamer Utility\t\t"
        renameBoijeFiles(boije_directory, json_file_path)
        
    if args_dictionary.get('download', 0):
        print "\t\t Starting Download Utility\t\t"
        scores_dictionary = dictionaryInit(json_file_path)
        scoreDownloader(scores_dictionary, boije_directory, json_file_path)


if __name__ == "__main__":
    main()

    
