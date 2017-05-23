from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey

from tuneful import app

engine = create_engine(app.config["DATABASE_URI"])
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)

class File(Base):
    __tablename__ = 'file'
    id = Column(Integer, primary_key=True)
    filename = Column(String(250))
    song = relationship("Song", uselist=False, backref="song_file")
    
    def as_dictionary(self):
        file_dict = {
            "id": self.id,
            "name": self.filename
        }
        return file_dict

class Song(Base):
    __tablename__ = 'song'
    id = Column(Integer, primary_key=True)
    
    file_id = Column(Integer, ForeignKey('file.id'), nullable=False)
    
    def as_dictionary(self):
        song_dict = {
            "id": self.id,
            "file": {
                "id": self.file_id,
                "name": self.song_file.filename
                }
            }
        return song_dict

#madness_file = File(filename="madness.mp3")
#madness = Song()
#madness_file.song = madness

#session.add(madness)
#session.commit()
