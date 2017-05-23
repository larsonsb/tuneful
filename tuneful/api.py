import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from . import database
from . import decorators
from . import app
from .database import session
from .utils import upload_path

post_schema = {
    "properties": {
        "file" : {"type" : "object"}
    },
    "required": ["file"]
}

post_file_schema = {
    "properties": {
        "id" : {"type" : "number"}
    },
    "required": ["id"]
}

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
    songs = session.query(database.Song)
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_post():
    data = request.json
    
    try:
        validate(data, post_schema)
        validate(data['file'], post_file_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
    
    file = session.query(database.File)
    file = file.filter(database.File.id == data['file']['id'])
    if len(file.all()) == 0:
        return Response(json.dumps(data), 404, mimetype="application/json")
    
    new_song = database.Song()
    new_song.file_id = data['file']['id']
    file.song = new_song
    session.add(new_song)
    session.commit()
    return Response(data, 201, mimetype="application/json")

@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(filename):
    return send_from_directory(upload_path(), filename)

@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
    file = request.files.get("file")
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")

    filename = secure_filename(file.filename)
    db_file = database.File(filename=filename)
    session.add(db_file)
    session.commit()
    file.save(upload_path(filename))

    data = db_file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")
