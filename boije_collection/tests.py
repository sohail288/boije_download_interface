import os, sys, shutil
import  unittest

import requests
from bs4 import BeautifulSoup as BSoup

from boije import BOIJE_SITE_INDEX_URL, DESTINATION_DIRECTORY,\
BOIJE_DIRECTORY_NAME, getOrCreateBoijeFolder, getOrCreateComposerFolder,\
boijeLink, getIndexSoup


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


class BoijeLetterIndexTests(unittest.TestCase):


    def testRetrieveLetterIndexSoup(self):
        index_to_check = 'c'

        soup = getIndexSoup(boijeLink(index_to_check))

        self.assertIn(unicode('<title>Boijes samling C</title>'), '%s'%soup.title)

    def testConvertRowEntiresToDictionary(self):
        self.fail("FINISH THIS TEST")

class DirectoryTests(unittest.TestCase):

    def setUp(self):
        self.path = os.path.join(DESTINATION_DIRECTORY, BOIJE_DIRECTORY_NAME)
        self.composer = 'carcassi'


    def testComposerDirectoryCreated(self):
        self.created_path = getOrCreateComposerFolder(self.path, self.composer)
        should_be_equal_to = os.path.join(self.path, self.composer)

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




if __name__ == '__main__':
    test_classes_to_run = [BoijeSiteRetrievalTests, DirectoryTests,BoijeLetterIndexTests ]
    loader = unittest.TestLoader()

    suites_list = []
    for test_class in test_classes_to_run:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    big_suite = unittest.TestSuite(suites_list)
    
    runner = unittest.TextTestRunner()
    results = runner.run(big_suite)
