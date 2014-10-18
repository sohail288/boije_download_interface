# -*- coding: utf-8 -*-
import os, sys, shutil, time, copy
import  unittest

import requests
from bs4 import BeautifulSoup as BSoup

from boije import BOIJE_SITE_INDEX_URL, DESTINATION_DIRECTORY,\
BOIJE_DIRECTORY_NAME, getOrCreateBoijeFolder, getOrCreateComposerFolder,\
boijeLink, getIndexSoup, convertIndexToDictionary, convertComposerName,\
convertScoreName, getScorePDF, saveScorePDF, createJsonFile, convertIndexToJson,\
convertJsonToDict, downloadAndSaveScore, updateJsonFile

class DirectorySetupAndRemovalMixin(object):
    #To be used only after all of these functions have been tested
    def setUp(self):
        self.directory_path = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
          
        
    def tearDown(self):
        for root, dirs, files in os.walk(self.directory_path):
            if BOIJE_DIRECTORY_NAME in root:
                shutil.rmtree(root)

class BoijeSiteRetrievalTests(unittest.TestCase):

    def testBoijeIndexReturns200(self):
        
        r = requests.get(BOIJE_SITE_INDEX_URL)
        
        status_code = r.status_code

        self.assertEqual(status_code, 200)

    def testBoijeLetterIndexReturns200(self):
        index_to_check = 'c'
        url_to_check = boijeLink(index_to_check)
        r = requests.get(url_to_check)

        status_code = r.status_code

        self.assertEqual('http://biblioteket.statensmusikverk.se/ebibliotek/boije/Boije_c.htm', url_to_check)
        self.assertEqual(status_code, 200)


class ScoreRetrieveAndStoreTests(DirectorySetupAndRemovalMixin, unittest.TestCase):

    def setUp(self):
        super(ScoreRetrieveAndStoreTests, self).setUp()
        self.score_name = 'Op_22_Trois_Sonates'
        self.composer = 'Carcassi_M'
        self.html = "pdf/Boije%2074.pdf"

    def testRetrieveScore(self):
        full_url = 'http://biblioteket.statensmusikverk.se/ebibliotek/boije/%s'%self.html

        downloaded_score = getScorePDF(self.html)
        score_pdf = downloaded_score.content
        status_code = downloaded_score.status_code

        #All pdfs start with PDF in the beginning
        self.assertEqual(full_url, downloaded_score.url)
        self.assertEqual(200, status_code)
        self.assertIn('%PDF-', score_pdf[0:5])

    def testStoreScore(self):
        downloaded_score = getScorePDF(self.html)
        create_boije_folder = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        create_composer_folder = getOrCreateComposerFolder(create_boije_folder, self.composer)
        downloaded_score = getScorePDF(self.html)
        path_to_score_should_be = os.path.join(create_composer_folder, '%s.pdf'%self.score_name)

        #The output of saveScorePDF will be a tuple (SUCCESS_CODE, PATH_TO_DOWNLOADED_SCORE)
        saving_score_to_folder = saveScorePDF(downloaded_score, self.score_name, create_composer_folder)
        truth_of_score, path_of_score = saving_score_to_folder

        self.assertTrue(truth_of_score)
        self.assertEqual(path_of_score, path_to_score_should_be)



class BoijeLetterIndexTests(unittest.TestCase):

    def testMakeComposerNameComputerReady(self):
        composer_1 = "Castillo, D. del"
        composer_2 = "     ."
        
        converted_composer_1 = convertComposerName(composer_1)
        converted_composer_2 = convertComposerName(composer_2)

        self.assertEqual('Castillo_D_del', converted_composer_1)
        self.assertEqual('anon', converted_composer_2)

    def testMakeScoreNameComputerReady(self):
        score_1 = 'Op. 24. Andante. Se: Gitarristische Vereinigung ... XVI. Jahrg. Nr 3. 1915'
        score_2 = 'Op. 22. Trois Sonates ...'
        score_3 = 'Oeuvres pour Guitare. No 1. Ètude.'
        score_4 = '”ERATO” Auswahl beliebter Gesänge ... No. 18. Santa Lucia! ...' 
        test_string  = '"órgão"'

        converted_score_1 = convertScoreName(score_1)
        converted_score_2 = convertScoreName(score_2)
        converted_score_3 = convertScoreName(score_3)
        converted_score_4 = convertScoreName(score_4)
        converted_score_5 = convertScoreName(test_string)

        self.assertEqual('Op_24_Andante_Se_Gitarristische_Vereinigung_XVI_Jahrg_Nr_3_1915', converted_score_1)
        self.assertEqual('Op_22_Trois_Sonates', converted_score_2)
        self.assertEqual('Oeuvres_pour_Guitare_No_1_Etude', converted_score_3)
        self.assertEqual('ERATO_Auswahl_beliebter_Gesange_No_18_Santa_Lucia', converted_score_4)    
        self.assertEqual('orgao', converted_score_5)
    
    def testRetrieveLetterIndexSoup(self):
        index_to_check = 'c'

        soup = getIndexSoup(boijeLink(index_to_check))

        self.assertIn(unicode('<title>Boijes samling C</title>'), '%s'%soup.title)

    def testConvertRowEntiresToDictionary(self):
        #checks to see if an index can be made into a dict
        #where dict = {'composer': {score1: (html, boije_number, downloaded)}, {score2: ...}}
        index_to_check = 'c'
        link_to_check = boijeLink(index_to_check)
        soup = getIndexSoup(link_to_check)

        dictionary_of_values = convertIndexToDictionary(soup)
        carcassi = dictionary_of_values.get('Carcassi_M')

        #remember that, the return of convertIndexToDictionary returns a dictioniary of composers
        #the dictionary will look like
        # {'composer': {'score1': ['html', 'boije', Downloaded], 'score2': [...]}, 'composer2': {...}...}
        self.assertEqual(len(dictionary_of_values['Calegari_F']), 2)
        self.assertIn('Carcassi_M', dictionary_of_values)
        self.assertIn('anon', dictionary_of_values)
        self.assertIn('Coste_N', dictionary_of_values)      
        #now check to see if some scores are found
        self.assertIn('Op_1_3_Sonates', dictionary_of_values['Carcassi_M'])
        self.assertIn('Op_13_4_Potpourris_des_plus_jolis_Airs_de_operas_de_Rossini', dictionary_of_values['Carcassi_M'])
        #now check to see if two of the above match the actual values from boije
        self.assertNotEqual(0, carcassi)
        self.assertEqual("pdf/Boije%2074.pdf", carcassi.get('Op_1_3_Sonates')[0])
        self.assertEqual("74", carcassi.get('Op_1_3_Sonates')[1])
        self.assertEqual(False, carcassi.get('Op_1_3_Sonates')[2])
        
    

#Okay I need a separate test to test whether a json file exists already


class DirectoryTests(unittest.TestCase):

    def setUp(self):
        self.path = os.path.join(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        self.composer = 'carcassi'


    def testComposerDirectoryCreated(self):
        should_be_equal_to = os.path.join(self.path, self.composer)

        self.created_path = getOrCreateComposerFolder(self.path, self.composer)
        created_path_exists = os.path.exists(self.created_path)

        self.assertTrue(created_path_exists)
        self.assertEqual(should_be_equal_to, self.created_path)

    def testBoijeDirectoryCreated(self):
        self.created_path = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        
        created_path_exists = os.path.exists(self.created_path)

        self.assertTrue(created_path_exists)
        self.assertEqual(self.path, self.created_path)


    def tearDown(self):
        for root, dirs, files in os.walk(self.path):
            if BOIJE_DIRECTORY_NAME in root:
                shutil.rmtree(root)


class CreateReadIndexTests(DirectorySetupAndRemovalMixin, unittest.TestCase):


    def testCreateIndexFile(self):
        json_file_name = 'boije_collection_test.json'
        create_boije_directory = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        #this test will check to see if a function exists to create a json index file
        file_path = os.path.join(self.directory_path, json_file_name)
        #file returns path or 0
        json_file_created = createJsonFile(json_file_name, create_boije_directory)

        self.assertEqual(file_path, json_file_created)
        

    def testJsonFileExists_soCreateShouldFail(self):
        json_file_name = 'boije_collection_test.json'
        create_boije_directory = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        create_json_file = createJsonFile(json_file_name, create_boije_directory)

        create_json_file_again = createJsonFile(json_file_name, create_boije_directory)

        self.assertEqual(0, create_json_file_again) 

class JSONFileTests(DirectorySetupAndRemovalMixin, unittest.TestCase):

    def testSaveIndexToJSONAndReadIt(self):
       #checks to see if an index that is converted to a dict can be written into a file with json format
        index_to_check = 'c'
        create_boije_directory = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        json_file_name = 'boije_collection_test.json'
        json_file_path = createJsonFile(json_file_name, create_boije_directory)
        link_to_check = boijeLink(index_to_check)
        soup = getIndexSoup(link_to_check)
        dictionary_of_values = convertIndexToDictionary(soup)
        #Our function will use a try/except block, that will will return a 1 or a 0 depending on success/failure
        dictionary_to_json = convertIndexToJson(dictionary_of_values, json_file_path)
        
        self.assertEqual(1, dictionary_to_json)
        json_file_size = os.path.getsize(json_file_path)
        json_file_exists = os.path.exists(json_file_path)
        self.assertTrue(json_file_exists)
        self.assertGreater(json_file_size, 0)
        
        
        #now we have a file that has something written to it.
        #We must  now check to see if when we read it, it will equate to dictionary_of_values

        convert_json_to_dict = convertJsonToDict(json_file_path)
        self.assertEqual(convert_json_to_dict, dictionary_of_values)


    def testReadJsonFile_modifyAnd_SaveIt(self):
        index_to_check = 'c'
        create_boije_directory = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        composer = 'Carcassi_M'
        score = 'Op_1_3_Sonates'
        json_file_name = 'boije_collection_test.json'
        json_file_path = createJsonFile(json_file_name, create_boije_directory)
        link_to_check = boijeLink(index_to_check)
        soup = getIndexSoup(link_to_check)
        dictionary_of_values = convertIndexToDictionary(soup)
        dictionary_to_json = convertIndexToJson(dictionary_of_values, json_file_path)
        convert_json_to_dict = convertJsonToDict(json_file_path)

        score_dictionary = copy.deepcopy(convert_json_to_dict)
        #make a function that wraps a try/except block
        #this function will need to copy the dictionary, and depending on whether 
        #a download succeeds.  It will update the 'downloaded' field from the dict
        #it will then return the dict
        carcassi = score_dictionary.get(composer)
        score_attributes = carcassi.get(score)
        html = score_attributes[0]
        
        self.assertFalse(score_attributes[2])

        #it will be better if this updating function takes in score attributes

        downloaded_file = downloadAndSaveScore(create_boije_directory, composer, score, score_attributes)
        
        self.assertTrue(downloaded_file)
        #set score_dictionary value to True
        score_dictionary[composer][score][2] = downloaded_file
        self.assertTrue(score_dictionary.get(composer).get(score)[0])
        
        self.assertNotEqual(score_dictionary[composer][score][2], convert_json_to_dict[composer][score][2])

        convert_dict_to_json = updateJsonFile(score_dictionary, json_file_path)
        convert_json_to_dict_again = convertJsonToDict(json_file_path)

        self.assertEqual(convert_json_to_dict_again, score_dictionary)
        

    def testDownloadScore_tryDownloadAgain_ResultsInError(self):
                        
        index_to_check = 'c'
        create_boije_directory = getOrCreateBoijeFolder(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        composer = 'Carcassi_M'
        score = 'Op_1_3_Sonates'
        json_file_name = 'boije_collection_test.json'
        json_file_path = createJsonFile(json_file_name, create_boije_directory)
        link_to_check = boijeLink(index_to_check)
        soup = getIndexSoup(link_to_check)
        dictionary_of_values = convertIndexToDictionary(soup)
        dictionary_to_json = convertIndexToJson(dictionary_of_values, json_file_path)
        convert_json_to_dict = convertJsonToDict(json_file_path)
        score_dictionary = copy.deepcopy(convert_json_to_dict) 
        score_attributes = convert_json_to_dict = score_dictionary.get(composer).get(score)

        download_file = downloadAndSaveScore(create_boije_directory, composer, score, score_attributes)

        self.assertTrue(download_file)
        #now to save json file and reload it.
        score_dictionary[composer][score][2] = download_file
        convert_dict_to_json = updateJsonFile(score_dictionary, json_file_path)
        convert_json_to_dict_again = convertJsonToDict(json_file_path)

        score_dictionary = copy.deepcopy(convert_json_to_dict_again)
        score_attributes = score_dictionary.get(composer).get(score)


        download_file = downloadAndSaveScore(create_boije_directory, composer, score,  score_attributes)

        self.assertFalse(download_file)

if __name__ == '__main__':
    test_classes_to_run = [BoijeSiteRetrievalTests, DirectoryTests, BoijeLetterIndexTests,
                            ScoreRetrieveAndStoreTests, 
                            CreateReadIndexTests, JSONFileTests]
    loader = unittest.TestLoader()

    suites_list = []
    for test_class in test_classes_to_run:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    big_suite = unittest.TestSuite(suites_list)
    
    runner = unittest.TextTestRunner()
    results = runner.run(big_suite)
