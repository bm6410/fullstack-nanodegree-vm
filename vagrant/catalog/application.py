from flask import Flask, render_template, url_for, redirect, request, flash, jsonify
from werkzeug.utils import secure_filename
from dbmodel import db, app, User, Poster, Director, Genre
from flask_httpauth import HTTPTokenAuth, HTTPBasicAuth
import random
import string
import os
import json

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from flask import session
import httplib2
from flask import make_response
import requests

auth = HTTPTokenAuth('Token')
# auth = HTTPBasicAuth()

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/img')
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posters.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db.init_app(app)

# let's just get the genres one time and use them everywhere
genres = db.session.query(Genre).all()


# home page
@app.route('/')
def show_home_page():
    return render_template('index.html', genres=genres)


# new poster page, protected behind login
@app.route('/new', methods=['GET', 'POST'])
# @auth.login_required
def add_new_poster():

    if 'username' not in session:
        return redirect(url_for('start'))

    else:

        # if we don't already have this folder to upload files to, create it
        if not (os.path.isdir(app.config['UPLOAD_FOLDER'])):
            os.mkdir(app.config['UPLOAD_FOLDER'])

        if request.method == 'POST':
            # if the director doesn't already exist, add to the db, then get the id
            director_name = request.form['director']
            director_obj = Director.query.filter_by(name=director_name).first()
            if director_obj is None:
                new_director = Director(name=director_name)
                db.session.add(new_director)
                db.session.commit()
                director_obj = new_director

            # upload the file ------------------------------------------------------
            # check if the post request has the file part
            if 'poster_img' not in request.files:
                flash('No file part')
                return "There is no file part here in the form"

            file = request.files['poster_img']

            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return "There is no file name here"

            try:
                filename = upload_file(file)
            except Exception as e:
                msg = "Couldn't upload your file"
                flash(msg)
                return msg

            # -----------------------------------------------------------------------

            # create the poster and add it to the db
            new_poster = Poster(
                title=request.form['title'],
                genre_id=request.form['genre'],
                director_id=director_obj.id,
                year=request.form['year'],
                poster_img=filename)

            db.session.add(new_poster)
            db.session.commit()
            return redirect(url_for('show_poster_info', poster_id=new_poster.id))
        else:
            return render_template('newposter.html', genres=genres)


# edit poster page, protected behind login
# @auth.login_required
@app.route('/<int:poster_id>/edit', methods=['GET', 'POST'])
def edit_poster(poster_id):

    if 'username' not in session:
        return redirect('/clientOAuth')
    else:
        # get the object, then update it
        poster_obj = Poster.query.filter_by(id=poster_id).first()

        if request.method == 'POST':
            if poster_obj is None:
                return "Something didn't work"
            else:
                poster_obj.title = request.form['title']
                poster_obj.genre_id = request.form['genre']
                poster_obj.year = request.form['year']
                # if the director doesn't already exist, create
                director_name = request.form['director']
                director_obj = Director.query.filter_by(name=director_name).first()
                if director_obj is None:
                    new_director = Director(name=director_name)
                    db.session.add(new_director)
                    db.session.commit()
                    director_obj = new_director

                poster_obj.director_id = director_obj.id

                # if the form thingy isn't blank and is different than what we had
                # before, let's delete what is there and upload the new one

                # upload the file ------------------------------------------------------
                # check if the post request has the file part
                if 'poster_img' not in request.files:
                    flash('No file part')
                    return "There is no file part here in the form"

                file = request.files['poster_img']
    #            if poster_obj.poster_img is not file.filename:
                # we have a new file

                # if user does not select file
                # submit an empty part without filename
                if file.filename == '':
                    flash('No selected file')
                    return "There is no file name here"

                try:
                    filename = upload_file(file)
                except Exception as e:
                    msg = "Couldn't upload your file"
                    flash(msg)
                    return msg

                # -----------------------------------------------------------------------
                # os.remove(os.path.join(app.config['UPLOAD_FOLDER'], poster_obj.poster_img))
                poster_obj.poster_img = filename

                db.session.commit()
                return redirect(url_for('show_poster_info', poster_id=poster_obj.id))

        else:
            return render_template('editPoster.html', posterObj=poster_obj, genres=genres)


# delete poster page, protected behind login
# @auth.login_required
@app.route('/<int:poster_id>/delete', methods=['GET', 'POST'])
def delete_poster(poster_id):
    if 'username' not in session:
        return redirect('/clientOAuth')
    else:
        if request.method == 'POST':
            # get the object, then delete it
            poster_obj = Poster.query.filter_by(id=poster_id).first()
            if poster_obj is None:
                return "Something didn't work"
            else:
                director_id = poster_obj.director_id
                db.session.delete(poster_obj)
                db.session.commit()

                # if that is the last film for the particular director we just
                # deleted, let's delete the director, too
                poster_by_director = Poster.query.filter_by(director_id=director_id).first()
                if not poster_by_director:
                    director_obj = Director.query.filter_by(id=director_id).first()
                    db.session.delete(director_obj)
                    db.session.commit()

                return render_template("index.html", genres=genres)
        else:
            return render_template('delete_poster.html', poster_id=poster_id)


# info for a poster
# todo:  change to Poster.query.get_or_404(poster_id) when switching to Model
@app.route('/<int:poster_id>')
def show_poster_info(poster_id):
    poster_obj = Poster.query.get(poster_id)
    if poster_obj is None:
        return "Something didn't work"
    else:
        return render_template('posterinfo.html', posterObj=poster_obj, referrer=request.referrer)


@app.route('/<int:poster_id>/JSON')
def show_poster_info_json(poster_id):
    poster_obj = Poster.query.get(poster_id)
    if poster_obj is None:
        return "Something didn't work"
    else:
        return jsonify(Poster=[poster_obj.serialize])


# page to display search results
@app.route('/searchResults/<string:category>/<int:id>')
def show_search_results(category, id):
    # find all the posters for the given category
    if category == 'genre':
        posters = Poster.query.filter_by(genre_id=id).all()
        redirect_route = 'show_genres'
    elif category == 'director':
        posters = Poster.query.filter_by(director_id=id).all()
        redirect_route = 'show_directors'
    else:
        posters = Poster.query.filter_by(year=id).all()
        redirect_route = 'show_years'

    if len(posters) > 0:
        return render_template('searchResults.html', posters=posters, root=APP_ROOT, referrer=request.referrer)
    else:
        # return "Nothing to see here"
        flash("We have no posters for that selection - please select another.")
        return redirect(url_for(redirect_route))


# show years
# show page with genres
@app.route('/category/genre')
def show_genres():
    return render_template('genres.html', genres=genres)


@app.route('/category/genre/JSON')
def show_genres_json():
    return jsonify(Genre=[i.serialize for i in genres])


# show page with genres
@app.route('/category/director')
def show_directors():
    directors = Director.query.order_by(Director.name)
    return render_template('directors.html', directors=directors)


@app.route('/category/director/JSON')
def show_directors_json():
    directors = Director.query.all()
    return jsonify(Director=[i.serialize for i in directors])


@app.route('/category/year')
def show_years():
    unique_years = Poster.query.distinct(Poster.year).group_by(Poster.year)
    return render_template('years.html', years=unique_years)


@app.route('/category/year/JSON')
def show_years_json():
    unique_years = Poster.query.distinct(Poster.year).group_by(Poster.year)
    return jsonify(Poster=[i.serialize for i in unique_years])


# all the posters in a category
@app.route('/category/<int:category_id>')
def show_posters_for_category(category_id):
    return render_template('category.html', category_id=category_id)


# utility functions ----------------------------------------------------------------------------------------------------
def allowed_file(filename):
    return '.' in filename and \
       filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename.replace(" ", "_"))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    else:
        raise Exception("Couldn't save your file")


# get the last url we were to send the user back
def redirect_url(default='show_home_page'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

# ----------------------------------------------------------------------------------------------------------------------

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


@app.route('/clientOAuth')
def start():
    # TODO: Fix this garbage
    # redirect_url() will always give us the default this way
    return render_template('clientOAuth.html', redirectURL=redirect_url())


@app.route('/oauth/<provider>', methods=['POST'])
def login(provider):
    # Parse the auth code
    auth_code = request.data
    print("Step 1 - Complete, received auth code %s" % auth_code)
    if provider == 'google':
        # Exchange for a token
        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        # # Verify that the access token is used for the intended user.
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # # Verify that the access token is valid for this app.
        if result['issued_to'] != CLIENT_ID:
            response = make_response(json.dumps("Token's client ID does not match app's."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        stored_credentials = session.get('access_token')
        stored_gplus_id = session.get('gplus_id')
        if stored_credentials is not None and gplus_id == stored_gplus_id:
            response = make_response(json.dumps('Current user is already connected.'), 200)
            response.headers['Content-Type'] = 'application/json'
            return response

        # store the credentials
        session['access_token'] = access_token
        session['gplus_id'] = gplus_id

        # Find User or make a new one

        # Get user info
        # h=httplib2.Http()
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

        # Make token
        token = user.generate_auth_token(600)
        print("*** user token: " + str(token))
#        request.headers['WWW-Authenticate'] = token
#         user.token = token.decode('ascii')
#         db.session.commit()

        # Send back token to the client
        return jsonify({'token': token.decode('ascii')})
#        return jsonify({'access_token': access_token})
        # return jsonify({'token': token.decode('ascii')}), 201, {'Location': url_for('show_home_page', _external=True)}

    else:
        return 'Unrecognized Provider'


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    print("In the logout function")
    access_token = session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect auth token is %s', access_token)
    print('User name is: ')
    print(session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del session['access_token']
        del session['gplus_id']
        del session['username']
        del session['email']
        del session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('show_home_page'))
    else:
        # TODO: go to error page with flash message
        response = make_response(json.dumps('Failed to revoke token for given user.'))
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == '__main__':
    app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    app.run(host='0.0.0.0', port=8082)
    # app.run(host = '0.0.0.0', port=8000)
