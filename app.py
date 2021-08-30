#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func,text
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.dialects import postgresql
import datetime
from models import db_setup,Artist,Venue,Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db = db_setup(app)

# TODO: connect to a local postgresql database

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  stamp=datetime.datetime.now()
  sql=text(F"""
  select jsonb_build_object('city',y.city,'venues',y.venues)
  from (
      select 
        T.city as city, 
        array_agg(jsonb_build_object('id', T.venue_id,'name', T.name, 'num_upcoming_shows', T.num_shows)) as venues 
      from ( 
          select 
            city,
            venue.name,
            count(*)filter(where shows.start_time > '{stamp}')  as num_shows,
            venue.id as venue_id 
          from
            venue FULL JOIN shows on venue.id = shows.venue_id
      group by city, venue.id,venue.name) 
  as T group by T.city) as y;""")
  result=db.engine.execute(sql)
  data=[]
  row=result.fetchone()
  while row != None:
    print(row)
    data.extend(list(row)) 
    row=result.fetchone()
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  stamp=datetime.datetime.now()
  search_term=request.form.get('search_term', '')
  data=db.session.query(
    Venue.id.label("id"),
    Venue.name.label("name"),
    func.count(Show.id).filter(Show.start_time<stamp).label("num_upcoming_shows")
  ).join(Show,isouter=True
  ).filter(Venue.name.ilike(F'%%{search_term}%%')
  ).group_by(Venue.id,Venue.name,Show.id).all()
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  print(venue_id)
  # TODO: replace with real venue data from the venues table, using venue_id
  stamp=datetime.datetime.now()
  shows=F"""
  (
    select 
    shows.venue_id as venue_id,
    count(*)filter(where shows.start_time > '{stamp}')as upcoming_shows_count,
    count(*)filter(where shows.start_time < '{stamp}')as past_shows_count,

      array_agg(jsonb_build_object(
        'artist_id',shows.artist_id,
        'artist_name',artist.name,
        'artist_image_link',artist.image_link,
        'start_time',shows.start_time ))filter(where shows.start_time > '{stamp}')as up_comming,

      array_agg(jsonb_build_object(
        'artist_id',shows.artist_id,
        'artist_name',artist.name,
        'artist_image_link',artist.image_link,
        'start_time',shows.start_time))filter(where shows.start_time < '{stamp}') as past
    from shows join artist on shows.artist_id=artist.id
    group by shows.venue_id
  ) as shows
  """
  venues=F"""
  select jsonb_build_object
  (
    'id',venue.id,
    'name',venue.name,
    'genres',coalesce(venue.genres,ARRAY[]::VARCHAR[]),
    'address',venue.address,
    'city',venue.city,
    'state',venue.state,
    'phone',venue.phone,
    'website',venue.website,
    'facebook_link',venue.facebook_link,
    'seeking_talent',venue.seeking_talent,
    'image_link',venue.image_link,
    'past_shows',coalesce(shows.past,ARRAY[]::jsonb[]), 
    'upcoming_shows',coalesce(shows.up_comming,ARRAY[]::jsonb[]),
    'past_shows_count',coalesce(shows.past_shows_count, 0),
    'upcoming_shows_count',coalesce(shows.upcoming_shows_count, 0)
  )
  from venue left join {shows} on venue.id=shows.venue_id
  where venue.id={venue_id}
  """
  result=db.engine.execute(venues).fetchone()
  if result:
    data=list(result)[0]
    return render_template('pages/show_venue.html', venue=data)
  else:
    return render_template('errors/404.html')
  




#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    new_venue=Venue(
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'],
      address=request.form['address'],
      phone=request.form['phone'],
      image_link=request.form['image_link'],
      genres=request.form.getlist('genres'),
      facebook_link=request.form['facebook_link'],
      website=request.form['website_link'],
      seeking_talent=(True if 'seeking_talent' in request.form else False),
      seeking_description=request.form['seeking_description']
    )
    db.session.add(new_venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('Failed to list Venue:' + request.form['name'] + '!')
  finally:
    db.session.close()
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    to_be_deleted_venue=Venue.query.get(venue_id)
    db.session.delete(to_be_deleted_venue)
    db.session.commit()
    flash('Venue was successfully deleted!')
  except:
    db.session.rollback()
    flash('Failed to delete the Venue!')
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists=db.session.query(Artist.name,Artist.id).all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term=request.form.get('search_term', '').lower()
  stamp=datetime.datetime.now()
  # count(artist.id),
  sql=F"""
  select 
  jsonb_build_object(
        'id',artist.id,
        'name',artist.name,
        'num_upcoming_shows',count(shows.id)filter(where shows.start_time < '{stamp}') )
  
  from artist left join shows on artist.id=shows.artist_id
  where LOWER(artist.name) like '%%{search_term}%%'  
  group by artist.id,artist.name;
  """
  result= db.engine.execute(sql)
  row=result.fetchone()
  data=[]
  while row != None:
    data.extend(list(row)) 
    row=result.fetchone()
  response={
    "count":len(data),
    "data":data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  
  stamp=datetime.datetime.now()
  shows=F"""
  (
    select 
    shows.artist_id as artist_id,
    count(*)filter(where shows.start_time > '{stamp}')as upcoming_shows_count,
    count(*)filter(where shows.start_time < '{stamp}')as past_shows_count,
      array_agg(jsonb_build_object(
        'venue_id',shows.venue_id,
        'venue_name',venue.name,
        'venue_image_link',venue.image_link,
        'start_time',shows.start_time ))filter(where shows.start_time > '{stamp}')as up_comming,
    
      array_agg(jsonb_build_object(
        'venue_id',shows.venue_id,
        'venue_name',venue.name,
        'venue_image_link',venue.image_link,
        'start_time',shows.start_time))filter(where shows.start_time < '{stamp}') as past
    from shows join venue on shows.venue_id=venue.id
    group by shows.artist_id
  ) as shows
  """
  artist=F"""
  select jsonb_build_object
  (
    'id',artist.id,
    'name',artist.name,
    'genres',coalesce(artist.genres,ARRAY[]::VARCHAR[]),
    'city',artist.city,
    'state',artist.state,
    'phone',artist.phone,
    'website',artist.website,
    'facebook_link',artist.facebook_link,
    'seeking_venue',artist.seeking_venue,
    'image_link',artist.image_link,
    'past_shows',coalesce(shows.past, ARRAY[]::jsonb[]),
    'upcoming_shows',coalesce(shows.up_comming, ARRAY[]::jsonb[]),
    'past_shows_count',coalesce(shows.past_shows_count, 0),
    'upcoming_shows_count',coalesce(shows.upcoming_shows_count, 0)
  )
  from artist left join {shows} on artist.id=shows.artist_id
  where artist.id={artist_id}
  """
  
  result=db.engine.execute(artist).fetchone()
  if result:
    data=list(result)[0]
    return render_template('pages/show_artist.html', artist=data)
  else:
    return render_template('errors/404.html')
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist=Artist.query.get(artist_id)
  print(artist)
  if artist!=None:
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.get(artist_id)
  try: 
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False 
    artist.seeking_description = request.form['seeking_description']
    
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('Failed to update Artist: ' + request.form['name'] + '!')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  if venue!=None: 
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)
  try: 
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website_link']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']
    
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('Failed to update Venue: ' + request.form['name'] + '!')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    new_artist=Artist(
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'],
      phone=request.form['phone'],
      image_link=request.form['image_link'],
      genres=request.form.getlist('genres'),
      facebook_link=request.form['facebook_link'],
      website=request.form['website_link'],
      seeking_venue=(True if 'seeking_venue' in request.form else False),
      seeking_description=request.form['seeking_description']
    )
    db.session.add(new_artist)
    db.session.commit()
   # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('Failed to list Artist:' + request.form['name'] + '!')
  finally:
    db.session.close()

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  stamp=datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
  print(stamp)
  data=db.session.query(
    Show.venue_id.label("venue_id"),
    Show.artist_id.label("artist_id"),
    Show.start_time.label("start_time"),
    Artist.name.label("artist_name"),
    Artist.image_link.label("artist_image_link"),
    Venue.name.label("venue_name")
  ).join(Artist).join(Venue).all()
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    new_show=Show(
      artist_id=request.form['artist_id'],
      venue_id=request.form['venue_id'],
      start_time=request.form['start_time']
    )
    stamp=datetime.datetime.now()
    
    db.session.add(new_show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('Failed to list the entered show!')
  finally:
    db.session.close()
  # on successful db insert, flash success

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
