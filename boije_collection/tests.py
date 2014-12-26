# -*- coding: utf-8 -*-
import os, sys, shutil, time, copy
import  unittest

import requests
from bs4 import BeautifulSoup as BSoup

from boije import BOIJE_SITE_INDEX_URL, DESTINATION_DIRECTORY, JSON_FILE_NAME,\
BOIJE_DIRECTORY_NAME, getOrCreateBoijeFolder, getOrCreateComposerFolder,\
boijeLink, getIndexSoup, convertIndexToDictionary, convertComposerName,\
convertScoreName, getScorePDF, saveScorePDF, createJsonFile, convertIndexToJson,\
convertJsonToDict, downloadAndSaveScore, updateJsonFile, getBoijeLetterIndices,\
consolidateIndicesToDictionary, boijeCollectionInit, dictionaryInit, scoreDownloader,\
getScorePath, loggingInit, getUserDesktop, renameBoijeFiles, getBoijeNumber,\
getScoreNameWithBoijeNumber, usage, getCommandLineArgs

##So we don't overwrite a users hard downloaded files
DESTINATION_DIRECTORY = './'
BOIJE_DIRECTORY_NAME = 'boije_test_directory'


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

    def testGetAllLetterIndexes(self):
        c_index = 'Boije_c.htm'
        ae_index = 'Boije_ae.htm'
        
        list_of_letter_indexes = getBoijeLetterIndices()

        self.assertIn(c_index, list_of_letter_indexes)
        self.assertIn(ae_index, list_of_letter_indexes)

class ScoreRetrieveAndStoreTests(DirectorySetupAndRemovalMixin, unittest.TestCase):

    def setUp(self):
        super(ScoreRetrieveAndStoreTests, self).setUp()
        self.score_name = 'Op_22_Trois_Sonates'
        self.composer = 'Carcassi_M'
        self.html = "pdf/Boije%2074.pdf"
        self.not_real_score = 'not_a_real_score'

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
        
        ##now we can test the getScorePath function, this function should return true
        returned_truth_of_get_score_path = getScorePath(self.composer, self.score_name, create_boije_folder)
        self.assertTrue(returned_truth_of_get_score_path)

        returned_false_of_get_score_path = getScorePath(self.composer, self.not_real_score, create_boije_folder)
        self.assertFalse(returned_false_of_get_score_path)

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
        
    
    def testConvertEveryIndexToASuperBigDictionary(self):
        indices = getBoijeLetterIndices()
        composer_1, score_1 = 'Carcassi_M', 'Op_3_Douze_petites_pieces_Pour_Guitare_ou_Lyre'
        composer_2, score_2 = 'Knjze_FM', 'Op_16_Ober_Oesterreicher'
        composer_3, score_3 = 'Zurfluh_A', 'Romance_sans_paroles'

        dictionary_of_every_composer = consolidateIndicesToDictionary(indices)
        
        self.assertIn(composer_1, dictionary_of_every_composer)
        self.assertIn(composer_2, dictionary_of_every_composer)
        self.assertIn(composer_3, dictionary_of_every_composer)
        self.assertIn(score_1, dictionary_of_every_composer.get(composer_1))
        self.assertIn(score_2, dictionary_of_every_composer.get(composer_2))
        self.assertIn(score_3, dictionary_of_every_composer.get(composer_3)) 

#Okay I need a separate test to test whether a json file exists already


class DirectoryTests(unittest.TestCase):

    def setUp(self):
        self.path = os.path.join(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        self.composer = 'carcassi'

    def testFindUserDesktop(self):
        '''
        will find user desktop using function getUserDesktop()
        all files will be saved to desktop/boije_collection
        '''
        path_should_contain = "Desktop"  

        path_returned = getUserDesktop()

        self.assertIn(path_should_contain, path_returned)

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
        

    def testJsonFileExistsSoCreateShouldFail(self):
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

        self.assertTrue(download_file)

class InitSequenceTests(DirectorySetupAndRemovalMixin, unittest.TestCase):

    def testInitSequenceCreatesJsonFile(self):
        json_file_path =  os.path.join(self.directory_path, JSON_FILE_NAME)
        boije_directory = self.directory_path
    
        returned_boije_directory, returned_json_file_path = boijeCollectionInit(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        
        self.assertEqual(json_file_path, returned_json_file_path)
        self.assertEqual(boije_directory, returned_boije_directory)

    def testDictionaryInitSequence(self):
        indices = getBoijeLetterIndices()
        dictionary_should_be = consolidateIndicesToDictionary(indices)
        boije_directory, json_file_path = boijeCollectionInit(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)        

        returned_dictionary = dictionaryInit(json_file_path)

        self.assertEqual(returned_dictionary, dictionary_should_be)

    def testDictionaryLoadsFromJson(self):
        index_to_check = 'c'
        boije_directory, json_file_path = boijeCollectionInit(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        link_to_check = boijeLink(index_to_check)
        convert_index_to_dictionary = convertIndexToDictionary(getIndexSoup(link_to_check))
        write_to_json_file = updateJsonFile(convert_index_to_dictionary, json_file_path)

        returned_dictionary = dictionaryInit(json_file_path)

        self.assertEqual(convert_index_to_dictionary, returned_dictionary) 

    def testDictionaryDoesNotLoadFromEmptyJson(self):
        indices = getBoijeLetterIndices()
        dictionary_should_be = consolidateIndicesToDictionary(indices)
        boije_directory, json_file_path = boijeCollectionInit(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)

        returned_dictionary = dictionaryInit(json_file_path)

        self.assertEqual(returned_dictionary, dictionary_should_be)

    def testScoreDownloader(self):
        index_to_check = 'c'
        boije_directory, json_file_path = boijeCollectionInit(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        link_to_check = boijeLink(index_to_check)
        convert_index_to_dictionary = convertIndexToDictionary(getIndexSoup(link_to_check))
        copy_of_dict = copy.deepcopy(convert_index_to_dictionary)
        ##lets check some composers
        composer_1 = 'Carcassi_M'
        composer_2 = 'anon'
        composer_3 = 'Cottin_A'
        carcassi_score_1 = convertScoreName('Op. 1. 3 Sonates.')
        carcassi_score_2 = convertScoreName('Op. 15. Tra la la. Air Varié …')
        carcassi_score_3 = convertScoreName('Op. 2. Trois Rondo Pour Guitare ou Lyre ...')
        anon_score_1 = convertScoreName('CHITARRISTA Moderna Pezzi Favoriti ...')
        anon_score_2 = convertScoreName('CIEBRA’s Hand-book for the Guitar ...')
        cottin_score_1 = convertScoreName('Ballade circassienne ...')
        cottin_score_2 = convertScoreName('Habanera.')
        #####  check paths, let's just make functions that check for paths
        path_to_carcassi_folder = os.path.join(self.directory_path, composer_1)
        path_to_anon_folder = os.path.join(self.directory_path, composer_2)
        path_to_cottin_folder = os.path.join(self.directory_path, composer_3) 

        returned_dictionary = scoreDownloader(copy_of_dict, boije_directory, json_file_path)

        #throughout the download process, the dictionary returned by downloaded should be different
        #There should be some truth values
        self.assertNotEqual(convert_index_to_dictionary, returned_dictionary)
        self.assertTrue(returned_dictionary.get(composer_1).get(carcassi_score_1)[2])
        self.assertTrue(returned_dictionary.get(composer_2).get(anon_score_1)[2])
        ##
        ## Now the file paths should exist.
        carcassi_score_1_exists = getScorePath(composer_1, carcassi_score_1, boije_directory)
        carcassi_score_2_exists = getScorePath(composer_1, carcassi_score_2, boije_directory)
        carcassi_score_3_exists = getScorePath(composer_1, carcassi_score_3, boije_directory)
        anon_score_1_exists = getScorePath(composer_2, anon_score_1, boije_directory)
        anon_score_2_exists = getScorePath(composer_2, anon_score_2, boije_directory)
        cottin_score_1_exists = getScorePath(composer_3, cottin_score_1, boije_directory)
        cottin_score_2_exists = getScorePath(composer_3, cottin_score_2, boije_directory)
        
        self.assertTrue(carcassi_score_1_exists)
        self.assertTrue(carcassi_score_2_exists)
        self.assertTrue(carcassi_score_3_exists)
        self.assertTrue(anon_score_1_exists)
        self.assertTrue(anon_score_2_exists)
        self.assertTrue(cottin_score_1_exists)
        self.assertTrue(cottin_score_2_exists)

class LoggerTests(DirectorySetupAndRemovalMixin, unittest.TestCase):

    def testLoggingFileCreated(self):
        '''
        Function that will create a logging file.  Test existence of logging file.
        '''
        boije_directory, json_file_path = boijeCollectionInit(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)

        logging_file_name, path_to_logger = loggingInit(boije_directory)
        ##print logging_file_name, path_to_logger
        logger_exists = os.path.exists(path_to_logger)
        

        self.assertTrue(logger_exists)

class RenamerUtilityTests(DirectorySetupAndRemovalMixin, unittest.TestCase):

    def setUp(self):
        super(RenamerUtilityTests, self).setUp()
        score_1_path = "./Boije 1.pdf"
        score_2_path = "./Boije 2.pdf"
        json_file_path = os.path.join(os.getcwd(), JSON_FILE_NAME)
        if not os.path.exists(score_1_path):
            # Download this score
            score_1_url = "pdf/Boije%201.pdf"
            score_1 = getScorePDF(score_1_url)
            saveScorePDF(score_1, "Boije 1", ".")

        if not os.path.exists("./Boije 2.pdf"):
            #Download this score
            score_2_url = "pdf/Boije%202.pdf"
            score_2 = getScorePDF(score_2_url) 
            saveScorePDF(score_2, "Boije 2", ".")
        if (not os.path.exists(json_file_path) or 
                not os.path.getsize(json_file_path)):
            json_file_path = createJsonFile(JSON_FILE_NAME, os.getcwd())
            dictionary_of_composers = dictionaryInit(json_file_path)
            update_json_file = updateJsonFile(
                dictionary_of_composers, json_file_path)

        shutil.copy(score_1_path, self.directory_path)
        shutil.copy(score_2_path, self.directory_path)
        shutil.copy(json_file_path, self.directory_path)

    def testGetScoreByBoijeNumber(self):
        score_1 = "Boije 1.pdf"
        score_2 = "Boije 2.pdf"
        boije_directory, json_file_path = boijeCollectionInit(
            DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        scores_dictionary = dictionaryInit(json_file_path)

        time.sleep(5) ##sleep
        score_1_number = getBoijeNumber(score_1)
        score_2_number = getBoijeNumber(score_2)
    
        # make sure a duplicate folder is not within the directory
        self.assertFalse(os.path.exists(
            "./boije_test_directory/boije_test_directory"))

        self.assertEqual("1", score_1_number)
        self.assertEqual("2", score_2_number)

        composer_1, score_1_name = getScoreNameWithBoijeNumber(scores_dictionary, score_1_number)
        composer_2, score_2_name = getScoreNameWithBoijeNumber(scores_dictionary, score_2_number)

        self.assertEqual(composer_1, "Aguado_D")
        self.assertEqual(score_1_name, "Op_1_Douze_valses")
        self.assertEqual(composer_2, "Aguado_D")
        self.assertEqual(score_2_name, "Op_2_Trois_rondos_brillants")

    

    def testRenameExistingFiles(self):
        composer = "Aguado_D"
        boije_directory, json_file_path = boijeCollectionInit(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        score_1_name = "Op_1_Douze_valses"
        score_2_name = "Op_2_Trois_rondos_brillants"

        renameBoijeFiles(boije_directory, json_file_path)

        score_1_renamed = os.path.exists(
            os.path.join(boije_directory, "%s/%s.pdf"%(composer, score_1_name))
            )
        score_2_renamed = os.path.exists(
            os.path.join(boije_directory, "%s/%s.pdf"%(composer, score_2_name))
            )
    
        #os.rename
        self.assertTrue(score_1_renamed)
        self.assertTrue(score_2_renamed)

        read_json_file_dict = convertJsonToDict(json_file_path)
        self.assertTrue(read_json_file_dict.get(composer).get(score_1_name)[2])
        self.assertTrue(read_json_file_dict.get(composer).get(score_1_name)[2])

class CommandLineArgsTests(unittest.TestCase):
        
    def testUsageDisplay(self):
        # test to make sure function exists and returns a value 0
        output_of_usage_function = usage()
        
        self.assertEqual(0, output_of_usage_function)

    def testGetArgs(self):
        """ Need to get arguments by pretend passing in a list of args """

        # First be able to set boije folder
        command_line_prompt_args =  ["--set-directory=./boije_test_directory", 
                                    "--rename", "--download"]

        parse_command_line_args = getCommandLineArgs(command_line_prompt_args)

        self.assertEqual(parse_command_line_args['directory'],
                        "./boije_test_directory")
        self.assertTrue(parse_command_line_args['rename'])
        self.assertTrue(parse_command_line_args['download'])

        command_line_prompt_args = ['-h', '-s' ,'./boije_test_directory',
                                    '-r', 'd']
        
        parse_command_line_args = getCommandLineArgs(command_line_prompt_args) 

        self.assertEqual(parse_command_line_args['directory'],
                        "./boije_test_directory")
        self.assertTrue(parse_command_line_args['rename'])
        self.assertTrue(parse_command_line_args['download'])

        
             
if __name__ == '__main__':
    test_classes_to_run = [
                           # BoijeSiteRetrievalTests, 
                            DirectoryTests, 
                            #BoijeLetterIndexTests, 
                            #ScoreRetrieveAndStoreTests, 
                            LoggerTests,                        
                            ##InitSequenceTests,
                            #CreateReadIndexTests, 
                            #JSONFileTests,
                            RenamerUtilityTests,
                            CommandLineArgsTests,
                            ]
    test_classes_to_run = test_classes_to_run
    loader = unittest.TestLoader()

    suites_list = []
    for test_class in test_classes_to_run:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    big_suite = unittest.TestSuite(suites_list)
    
    runner = unittest.TextTestRunner()
    results = runner.run(big_suite)
