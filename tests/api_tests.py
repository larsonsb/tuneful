import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import database
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())
    
    def test_get_empty_songs(self):
        """ Getting songs from an empty database """
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/json")]
        )
    
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
    
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data, [])

    def test_get_songs(self):
        """ Getting songs from a populated database """
        fileA = database.File(filename="example A.mp3")
        songA = database.Song()
        fileA.song = songA
        fileB = database.File(filename="example B.mp3")
        songB = database.Song()
        fileB.song = songB

        session.add_all([fileA, fileB])
        session.commit()
        
        response = self.client.get("/api/songs", headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(data), 2)
        
        songA = data[0]
        self.assertEqual(songA["file"]["name"], "example A.mp3")

        songB = data[1]
        self.assertEqual(songB["file"]["name"], "example B.mp3")

    def test_post_malformed_data(self):
        """ Post malformed data """
        post_data = {
            "misspelled_file": {
                "id": 7
            }
        }
        response = self.client.post("/api/songs", data=json.dumps(post_data), content_type="application/json", headers=[("Accept", "application/json")])
        self.assertEqual(response.status_code, 422)

    def test_post_non_existent_song(self):
        """ Getting non-existant file """
        post_data = {
            "file": {
                "id": 7
            }
        }
        
        files = session.query(database.File)
        files = files.filter(database.File.id == post_data['file']['id'])
        self.assertEqual(len(files.all()), 0)
        
        response = self.client.post("/api/songs", data=json.dumps(post_data), content_type="application/json", headers=[("Accept", "application/json")])
        self.assertEqual(response.status_code, 404)
        
    def test_post_song(self):
        """ Getting existing file """
        fileA = database.File(filename="example A.mp3")
        session.add(fileA)
        session.commit()
        
        post_data = {
            "file": {
                "id": 1
            }
        }
    
        files = session.query(database.File)
        files = files.filter(database.File.id == post_data['file']['id'])
        self.assertEqual(len(files.all()), 1)
        
        response = self.client.post("/api/songs", data=json.dumps(post_data), content_type="application/json", headers=[("Accept", "application/json")])
        self.assertEqual(response.status_code, 201)
        
        song = session.query(database.Song)
        song = song.filter(database.Song.file_id == post_data['file']['id'])
        self.assertEqual(len(song.all()), 1)
