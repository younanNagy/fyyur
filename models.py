
from sqlalchemy.dialects import postgresql
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate



db = SQLAlchemy()
def db_setup(app):
    app.config.from_object('config')
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)

    return db
class Show(db.Model):
    __tablename__='shows'
    id=db.Column(db.Integer,primary_key=True)
    venue_id=db.Column(db.Integer,db.ForeignKey('venue.id'))
    artist_id=db.Column(db.Integer,db.ForeignKey('artist.id'))
    start_time=db.Column(db.DateTime,)
    venue=db.relationship("Venue",back_populates="shows")
    artist=db.relationship("Artist",back_populates="shows")

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website=db.Column(db.String(120))
    seeking_talent=db.Column(db.Boolean,default=False)
    seeking_description=db.Column(db.Text)
    image_link=db.Column(db.Text)
    genres=db.Column(postgresql.ARRAY(db.String))

    shows=db.relationship("Show",back_populates="venue")
    
    # @classmethod
    # def 
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
  
class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres=db.Column(postgresql.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website=db.Column(db.String(120))
    seeking_venue=db.Column(db.Boolean,default=False)
    seeking_description=db.Column(db.Text)
    image_link=db.Column(db.Text)

    shows=db.relationship("Show",back_populates="artist")
#     # TODO: implement any missing fields, as a database migration using Flask-Migrate

