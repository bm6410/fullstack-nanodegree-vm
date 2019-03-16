"""Application.py"""
# TODO - clean up urls to match json endpoints

import sys
sys.path.insert(0, '/var/www/html')

from flask import render_template, url_for, redirect, request, flash, jsonify
from flask_compress import Compress
from werkzeug.utils import secure_filename
from dbmodel import db, app, User, Poster, Director, Genre
from flask_httpauth import HTTPTokenAuth
import random
import string
import os
import json
from werkzeug.exceptions import UnsupportedMediaType
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from flask import session
import httplib2
from flask import make_response
import requests
from PIL import Image
import logging


auth = HTTPTokenAuth('Token')

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/img')
PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(PROJECT_ROOT, 'client_secrets.json')
CLIENT_ID = json.load(open(json_url))['web']['client_id']
# compression for site resources - method borrowed from here:
# https://damyanon.net/post/flask-series-optimizations/
COMPRESS_MIMETYPES = [
    'text/html',
    'text/css',
    'text/xml',
    'application/json',
    'application/javascript']
COMPRESS_LEVEL = 6
COMPRESS_MIN_SIZE = 500

logging.basicConfig(level=logging.DEBUG)

app.debug = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Compress(app)
db.init_app(app)

# let's just get the genres one time and use them everywhere
genres = db.session.query(Genre).all()


# display the home page
@app.route('/')
def show_home_page():
    """Displays the home page for the application."""

    session['redirect_route'] = request.path
    session['current_category_url'] = request.path
    return render_template('index.html')


# display the add new poster form
@app.route('/new', methods=['GET', 'POST'])
def add_new_poster():
    """Displays and processes the form to add a new poster entry.

    Protected behind login."""

    # ensure user is logged in first
    if 'username' not in session:
        return redirect(url_for('start'))
    else:

        try:
            # create the upload folder if we don't already have
            if not (os.path.isdir(app.config['UPLOAD_FOLDER'])):
                os.mkdir(app.config['UPLOAD_FOLDER'])

            if request.method == 'POST':

                # upload the file - any errors here will end up throwing an
                # exception and rolling everything back

                # check if the post request has the file part
                if 'poster_img' not in request.files:
                    raise Exception(
                        "There was an error retrieving the file from the form"
                    )

                # will throw an UnsupportedMediaFile exception if the file
                # isn't one we can accept or we can't upload
                # will throw an IOError if we couldn't create the thumbnail
                file = request.files['poster_img']
                filename = upload_poster_img(file)

                # start a savepoint here, so we can rollback all of it if
                # this fails
                # db.session.begin_nested()

                # if the director doesn't already exist, add to the db, then
                # get the id
                director_name = request.form['director']
                director_obj = \
                    Director.query.filter_by(name=director_name).first()
                if director_obj is None:
                    new_director = Director(name=director_name)
                    db.session.add(new_director)
                    db.session.commit()
                    director_obj = new_director

                # create the poster and add it to the db
                new_poster = Poster(
                    title=request.form['title'],
                    genre_id=request.form['genre'],
                    director_id=director_obj.id,
                    year=request.form['year'],
                    poster_img=filename,
                    user_id=session['user_id']
                )

                db.session.add(new_poster)
                db.session.commit()

                # poster was created, let's show the user a success message
                flash(
                    '"' +
                    request.form['title'] +
                    '" created successfully!',
                    'success'
                )
                logging.info(request.form['title'] + ' created.  Redirecting')
                return redirect(
                    url_for('show_poster_info', poster_id=new_poster.id)
                )

            else:
                return render_template('newposter.html', genres=genres)

        except Exception as e:
            db.session.rollback()
            flash(e, 'error')
            # TODO: should stop the submit so the user doesn't lose the
            #  data they have entered
            return render_template('newposter.html', genres=genres)


# displays edit poster form
@app.route('/<int:poster_id>/edit', methods=['GET', 'POST'])
def edit_poster(poster_id):
    """Displays and processes form for user to edit an entry.

    Protected behind login
    Takes a poster_id as an argument."""

    # ensure user is logged in first
    if 'username' not in session:
        return redirect('/clientOAuth')

    else:
        logging.debug("User is logged in - in edit")

        # the wrong user is logged in
        poster_obj = Poster.query.filter_by(id=poster_id).first()
        if poster_obj.user_id != session['user_id']:
            flash('You are not authorized to edit this item. ' +
                  'Please edit one of your own items.', 'error')
            return redirect(url_for('show_poster_info', poster_id=poster_id))

        else:

            try:
                # get the object, then update it
                poster_obj = Poster.query.filter_by(id=poster_id).first()

                if request.method == 'POST':
                    if poster_obj is None:
                        # we shouldn't get here, something bad happened
                        flash('The poster could not be edited', 'error')
                        return redirect(url_for("show_home_page"))
                    else:

                        # start transaction in case we need to rollback
                        # db.session.begin_nested()

                        poster_obj.title = request.form['title']
                        poster_obj.genre_id = request.form['genre']
                        poster_obj.year = request.form['year']

                        old_director_id = poster_obj.director_id

                        # if the director doesn't already exist, create
                        director_name = request.form['director']
                        director_obj = \
                            Director.query.filter_by(
                                name=director_name).first()
                        if director_obj is None:
                            new_director = Director(name=director_name)
                            db.session.add(new_director)
                            db.session.commit()
                            director_obj = new_director

                        poster_obj.director_id = director_obj.id

                        # if the img field isn't blank and is different
                        # than we had before, let's delete what is there and
                        # upload the new one
                        old_file_name = poster_obj.poster_img
                        new_file_name = request.form['poster_img_name']
                        logging.debug("New file is " + new_file_name)
                        if new_file_name != old_file_name:
                            # we have a new file, let's upload

                            # check if the post request has the file part
                            if 'poster_img' not in request.files:
                                flash('No file part')
                                return "There is no file part here in the form"

                            file = request.files['poster_img']

                            # if user does not select file submit an empty part
                            # without filename
                            if file.filename == '':
                                flash('No selected file')
                                return "There is no file name here"

                            try:
                                filename = upload_poster_img(file)
                            except UnsupportedMediaType as e:
                                flash(e, 'error')
                                return render_template(
                                    'editPoster.html',
                                    posterObj=poster_obj,
                                    genres=genres
                                )

                            poster_obj.poster_img = filename

                            # if nobody else needs it, remove the old file
                            old_poster_img = \
                                Poster.query.filter_by(
                                    poster_img=old_file_name
                                ).first()
                            if old_poster_img is None:
                                # safe to delete it...no one else needs it
                                delete_poster_img(old_file_name)

                        db.session.commit()

                        # if that is the last film for the old director we just
                        # deleted, let's delete the director, too
                        if old_director_id != director_obj.id:
                            poster_by_director = \
                                Poster.query.filter_by(
                                    director_id=old_director_id).first()
                            if not poster_by_director:
                                old_director_obj = Director.query.filter_by(
                                    id=old_director_id).first()
                                db.session.delete(old_director_obj)
                                db.session.commit()

                        # poster was edited successfully, let's show the
                        # user a success message
                        flash(
                            '"' +
                            request.form['title'] +
                            '" edited successfully!',
                            'success'
                        )
                        return redirect(
                            url_for(
                                'show_poster_info', poster_id=poster_obj.id
                            )
                        )

                else:
                    logging.debug("Returning edit form")

                    return render_template(
                        'editposter.html', posterObj=poster_obj, genres=genres
                    )

            except Exception as e:
                db.session.rollback()
                flash(e, 'error')
                return redirect(
                    url_for('show_poster_info', poster_id=poster_id)
                )


# delete poster page, protected behind login
@app.route('/<int:poster_id>/delete', methods=['GET', 'POST'])
def delete_poster(poster_id):
    """Displays and processes the form to delete a poster.

    Protected behind login
    Takes a poster_id as an argument."""

    # ensure user is logged in first
    if 'username' not in session:
        return redirect('/clientOAuth')

    else:
        # the wrong user is logged in
        poster_obj = Poster.query.filter_by(id=poster_id).first()
        if poster_obj.user_id != session['user_id']:
            flash('You are not authorized to delete this item. ' +
                  'Please delete one or your own items.', 'error')
            return redirect(url_for('show_poster_info', poster_id=poster_id))

        else:

            try:
                # user is logged in - get the object from the db, delete it,
                # then clean up director and image info
                poster_obj = Poster.query.filter_by(id=poster_id).first()
                if poster_obj is None:
                    # we shouldn't get here, but if we do, something bad
                    # happened
                    flash('The poster could not be deleted', 'error')
                    return redirect(url_for("show_home_page"))

                elif request.method == 'POST':

                    # start a transaction, in case we have to rollback
                    # db.session.begin_nested()

                    # get the object, then delete it
                    director_id = poster_obj.director_id
                    db.session.delete(poster_obj)

                    # if that is the last film for the particular director
                    # we just deleted, let's delete the director, too
                    poster_by_director = Poster.query.filter_by(
                        director_id=director_id).first()
                    if not poster_by_director:
                        director_obj = Director.query.filter_by(
                            id=director_id).first()
                        db.session.delete(director_obj)

                    # if nobody else needs it, remove the old poster file
                    old_poster_img = Poster.query.filter_by(
                        poster_img=poster_obj.poster_img).first()
                    if old_poster_img is None:
                        # safe to delete it...no one else needs it
                        delete_poster_img(poster_obj.poster_img)

                    db.session.commit()

                    flash(
                        'Successfully deleted "' +
                        poster_obj.title +
                        '"', 'success'
                    )
                    return render_template("index.html", genres=genres)
                else:
                    return render_template(
                        'deleteposter.html',
                        poster_id=poster_id,
                        poster_title=poster_obj.title
                    )

            except Exception as e:
                db.session.rollback()
                flash(e, 'error')
                logging.debug('Exception thrown in delete_poster(): %s', e)
                return redirect_url(url_for(edit_poster, poster_id=poster_id))


# info for a single poster with the given ID
@app.route('/<int:poster_id>')
def show_poster_info(poster_id):
    """Displays the info for a specific poster.

    Takes a poster_id for an argument."""

    poster_obj = Poster.query.get(poster_id)
    if poster_obj is None:
        # we should never get here, but just in case...
        flash('The poster you requested could not be found.', 'error')
        return redirect(url_for("show_home_page"))
    else:
        return render_template('posterinfo.html', posterObj=poster_obj)


# info for a single poster with the given ID in JSON format
@app.route('/posters/<int:poster_id>/JSON/v1/')
@app.route('/posters/<int:poster_id>/json/v1/')
def show_poster_info_json(poster_id):
    """Returns the info for a specific poster in JSON format.

    Takes a poster_id for an argument."""

    poster_obj = Poster.query.get(poster_id)
    if poster_obj is None:
        return "Couldn't return any info for poster with id=" + str(poster_id)
    else:
        return jsonify(Poster=[poster_obj.serialize])


# shows all posters in the db in JSON format only
@app.route('/posters/JSON/v1/')
@app.route('/posters/json/v1/')
def show_all_posters():
    """Returns all the posters in the database.

    This only returns JSON"""

    posters = Poster.query.all()
    if posters is None:
        return "Couldn't retrieve the posters"
    else:
        return jsonify(Poster=[i.serialize for i in posters])


# page to display search results for a category with the given ID
@app.route('/searchResults/<string:category>/<int:category_id>')
def show_search_results(category, category_id):
    """Displays the search results for a given category.

    Args:   category as a string ('genre', 'director', 'year')
            category_id as an int"""

    # find all the posters for the given category
    if category == 'genre':
        posters = Poster.query.order_by(Poster.title).filter_by(
            genre_id=category_id).all()
        title = "Genres"
        search_heading = Genre.query.filter_by(id=category_id).first().name
    elif category == 'director':
        posters = \
            Poster.query.order_by(Poster.title).filter_by(
                director_id=category_id).all()
        # we can have a case where the director chosen has been deleted
        # if so, let's just go back to the
        # directors page
        if len(posters) == 0:
            return redirect(url_for('show_directors'))
        title = "Directors"
        search_heading = Director.query.filter_by(id=category_id).first().name
    else:
        posters = \
            Poster.query.order_by(Poster.title).filter_by(
                year=str(category_id)).all()
        title = "Years"
        search_heading = category_id

    # build navigation url so our back buttons work correctly
    session['current_category_url'] = request.path

    if len(posters) > 0:
        return render_template(
            'searchResults.html',
            posters=posters,
            title=title,
            search_heading=search_heading
        )
    else:
        flash(
            'We have no posters for that selection - please select another.',
            'error'
        )
        return redirect(session['redirect_route'])


# page to display search results for a category with the given ID
# results in JSON
@app.route('/searchResults/<string:category>/<int:category_id>/JSON/v1/')
@app.route('/searchResults/<string:category>/<int:category_id>/json/v1/')
def show_search_results_json(category, category_id):
    """Returns the search results in JSON format.

    Args:   category as a string ('genre', 'director', 'year')
            category_id as an int"""

    # find all the posters for the given category
    if category == 'genre':
        posters = Poster.query.order_by(Poster.title).filter_by(
            genre_id=category_id).all()
    elif category == 'director':
        posters = \
            Poster.query.order_by(Poster.title).filter_by(
                director_id=category_id).all()
    else:
        posters = \
            Poster.query.order_by(Poster.title).filter_by(
                year=category_id).all()

    return jsonify(Poster=[i.serialize for i in posters])


# show page with genres
@app.route('/category/genre')
def show_genres():
    """Displays the page with the list of genres."""

    session['redirect_route'] = request.path
    return render_template('genres.html', genres=genres)


# return genres in JSON format
@app.route('/genres/JSON/v1/')
@app.route('/genres/json/v1/')
def show_genres_json():
    """Returns the list of genres in JSON format."""

    return jsonify(Genre=[i.serialize for i in genres])


# show page with directors
@app.route('/category/director')
def show_directors():
    """Displays the page with the available directors."""

    session['redirect_route'] = request.path
    directors = Director.query.order_by(Director.name)
    return render_template('directors.html', directors=directors)


# return directors in JSON format
@app.route('/directors/JSON/v1/')
@app.route('/directors/json/v1/')
def show_directors_json():
    """Returns the list of available directors in JSON format."""

    directors = Director.query.order_by(Director.name)
    return jsonify(Director=[i.serialize for i in directors])


# show page with years
@app.route('/category/year')
def show_years():
    """Displays the page with the available years."""

    session['redirect_route'] = request.path
    unique_years = Poster.query.distinct(Poster.year).group_by(
        Poster.year, Poster.id
    )
    return render_template('years.html', years=unique_years)


# return available years in JSON format
@app.route('/years/JSON/v1/')
@app.route('/years/json/v1/')
def show_years_json():
    """Returns the available years in JSON format."""

    unique_years = Poster.query.distinct(Poster.year).group_by(Poster.year)
    years = []
    for poster in unique_years:
        years.append(poster.year)

    return json.dumps(years)


# utility functions ------------------------------------------------------

# checks that the file matches the allowed file types
# Borrowed from the Flask pages on Uploading Files
def allowed_file(filename):
    """Checks that the file has an allowed extension.

    Takes the filename as an argument."""

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# uploads the poster image to the server, and creates a thumbnail for use
# in search results
# The basics of the thumbnail code comes from the Pillow documentation
def upload_poster_img(file):
    """Uploads a file to the server's filesystem.

    Takes the file as an argument."""

    # TODO: optimum size for the page is 540x816.  if the pic is larger,
    #  resize before saving
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename.replace(" ", "_"))
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(full_filename)

        # create a thumbnail image for search displays
        size = (200, 325)
        thumbnail = os.path.splitext(full_filename)[0] + ".thumbnail"
        try:
            im = Image.open(full_filename)
            img_copy = im.copy()
            img_copy.thumbnail(size)
            img_copy.save(thumbnail, "JPEG")

        except IOError:
            raise IOError(
                "Couldn't create a thumbnail of your image.  Please try again."
            )

        return filename
    else:
        raise UnsupportedMediaType(
            "Couldn't save your image.  " +
            "Please make sure to upload a .jpg, .jpeg, .png, or .gif file.")


# delete the poster image file from the server
def delete_poster_img(filename):
    """Deletes the given poster from the server's filesystem.

    Takes the filename as an argument.
    Will also remove the associated thumbnail image, if it exists."""

    full_filename = str(app.config['UPLOAD_FOLDER'] + "/" + filename)
    logging.debug('Full filename is  %s', full_filename)

    if os.path.exists(full_filename):
        os.remove(full_filename)

        # delete the thumbnail, too
        path_to_thumbnail = str.rsplit(full_filename, '.')[0] + ".thumbnail"
        logging.debug('PATH TO THUMBNAIL - %s', path_to_thumbnail)
        os.remove(path_to_thumbnail)
    else:
        raise Exception(full_filename + " does not exist.")


# get the last url we were to send the user back
def redirect_url(default='show_home_page'):
    """Returns the url of the last page the user was on."""

    return request.args.get('next') or \
        request.referrer or \
        url_for(default)


# Authentication code
#
# @auth.verify_token
# def verify_token(token):
#     print("IN verify_token - TOKEN = " + token)
#     print("TOKEN in Session - " + str(session.get('auth_token')))
#     user_id = User.verify_auth_token(str(session.get('auth_token')))
#     print("We got a user ID - " + str(user_id))
#     if user_id:
#         user = db.session.query(User).filter_by(id = user_id).one()
#     else:
#         return False
#
#     g.user = user
#     return True


# sends the user to the login page
@app.route('/clientOAuth')
def start():
    """Displays the login page to the user."""

    return render_template('clientOAuth.html', redirectURL=redirect_url())


# log in the user via Google accounts.
# stores the user info in the session so other methods can verify
# user is logged in
# Much of this code was borrowed from Udacity example code
@app.route('/oauth/<provider>', methods=['POST'])
def login(provider):
    """Logs in the user with the given provider.

    Args:   provider as string (currently only supports 'google')
    Stores the user info in the session."""

    # Parse the auth code
    auth_code = request.data
    if provider == 'google':
        # Exchange for a token
        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = \
                flow_from_clientsecrets(json_url, scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            response = \
                make_response(
                    json.dumps('Failed to upgrade the authorization code.'),
                    401
                )
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = \
            ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
             % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        # # Verify that the access token is used for the intended user.
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = \
                make_response(
                    json.dumps("Token's user ID doesn't match given user ID."),
                    401
                )
            response.headers['Content-Type'] = 'application/json'
            return response

        # # Verify that the access token is valid for this app.
        if result['issued_to'] != CLIENT_ID:
            response = \
                make_response(
                    json.dumps("Token's client ID does not match app's."), 401
                )
            response.headers['Content-Type'] = 'application/json'
            return response

        stored_credentials = session.get('access_token')
        stored_gplus_id = session.get('gplus_id')
        if stored_credentials is not None and gplus_id == stored_gplus_id:
            response = \
                make_response(
                    json.dumps('Current user is already connected.'), 200
                )
            response.headers['Content-Type'] = 'application/json'
            return response

        # store the credentials
        session['access_token'] = access_token
        session['gplus_id'] = gplus_id

        # Find User or make a new one

        # Get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        name = data['name']
        picture = data['picture']
        email = data['email']

        # store user info
        session['username'] = name
        session['email'] = email
        session['picture'] = picture

        # see if user exists, if it doesn't make a new one
        user = db.session.query(User).filter_by(email=email).first()
        if not user:
            user = User(username=name, picture=picture, email=email)
            db.session.add(user)
            db.session.commit()

        session['user_id'] = user.id

        # Make token - not really using this for anything anymore (since I
        # couldn't figure out how to store it
        token = user.generate_auth_token(600)
#        request.headers['WWW-Authenticate'] = token
#         user.token = token.decode('ascii')
#         db.session.commit()

        # Send back token to the client
        flash('You are now logged in as ' + name, 'success')
        return jsonify({'token': token.decode('ascii')})

    else:
        return 'Unrecognized Provider'


# revokes the token with Google and removes the user info from the session
# the bulk of this code was borrowed from Udacity
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logs out the user.

    Currently only supports logging out from google.
    Removes the user information from the session."""

    access_token = session.get('access_token')
    if access_token is None:
        response = \
            make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    logging.debug('In gdisconnect auth token is %s', access_token)
    logging.debug('User name is: ' + session['username'])

    url = \
        'https://accounts.google.com/o/oauth2/revoke?token=%s' % \
        session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    # print('result is ' + str(result))
    if result['status'] == '200':
        del session['access_token']
        del session['gplus_id']
        del session['username']
        del session['email']
        del session['picture']
        del session['user_id']

        flash('You have successfully logged out!', 'success')

    else:
        flash(
            'We were unable to log you out of Google.  Please try again.',
            'error'
        )

    # return redirect(url_for('show_home_page'))
    return "Successfully logged out"


if __name__ == '__main__':
    app.config['SECRET_KEY'] = \
        ''.join(
            random.choice(
                string.ascii_uppercase + string.digits
            ) for x in range(32)
        )
    # app.run(host='0.0.0.0', port=8082)
    # app.run()

    port = int(os.environ.get("PORT", 8082))
    app.run(
        host="0.0.0.0",
        port=port,
    )
