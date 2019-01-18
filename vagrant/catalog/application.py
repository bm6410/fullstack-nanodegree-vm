from flask import Flask, render_template, url_for, redirect, request, flash, jsonify
from dbmodel import db, app, Poster, Director, Genre
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random, string


app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posters.db'
db.init_app(app)

# let's just get the genres one time and use them everywhere
genres = db.session.query(Genre).all()


# home page
@app.route('/')
def showHomePage():
    return render_template('index.html', genres = genres)

# new poster page, protected behind login
@app.route('/new', methods=['GET', 'POST'])
#@auth.login_required
def addNewPoster():
    if request.method == 'POST':
        # if the director doesn't already exist, add to the db, then get the id
        director_name = request.form['director']
        directorObj = Director.query.filter_by(name = director_name).first()
        if directorObj is None:
            newDirector = Director(name = director_name)
            db.session.add(newDirector)
            db.session.commit()
            directorObj = newDirector

        # create the poster and add it to the db
        newPoster = Poster(title = request.form['title'],
            genre_id = request.form['genre'],
            director_id = directorObj.id,
            year = request.form['year'])
        db.session.add(newPoster)
        db.session.commit()
        return redirect(url_for('showPosterInfo', poster_id = newPoster.id))
    else:
        return render_template('newposter.html', genres = genres)

# edit poster page, protected behind login
#@auth.login_required
@app.route('/<int:poster_id>/edit', methods=['GET', 'POST'])
def editPoster(poster_id):
    # get the object, then update it
    posterObj = Poster.query.filter_by(id = poster_id).first()

    if request.method == 'POST':
        if posterObj is None:
            return "Something didn't work"
        else:
            posterObj.title = request.form['title']
            posterObj.genre_id = request.form['genre']
            posterObj.year = request.form['year']
            # if the director doesn't already exist, create
            director_name = request.form['director']
            directorObj = Director.query.filter_by(name = director_name).first()
            if directorObj is None:
                newDirector = Director(name = director_name)
                db.session.add(newDirector)
                db.session.commit()
                directorObj = newDirector

            posterObj.director_id = directorObj.id
            db.session.commit()
            return redirect(url_for('showPosterInfo', poster_id = posterObj.id))

    else:
        return render_template('editPoster.html', posterObj = posterObj, genres = genres)

#delete poster page, protected behind login
#@auth.login_required
@app.route('/<int:poster_id>/delete', methods=['GET', 'POST'])
def deletePoster(poster_id):
    if request.method == 'POST':
        # get the object, then delete it
        posterObj = Poster.query.filter_by(id = poster_id).first()
        if posterObj is None:
            return "Something didn't work"
        else:
            db.session.delete(posterObj)
            db.session.commit()
            print "We deleted that poster"
            return render_template("index.html", genres = genres)
    else:
        return render_template('deletePoster.html', poster_id = poster_id)

# info for a poster
# todo:  change to Poster.query.get_or_404(poster_id) when switching to Model
@app.route('/<int:poster_id>')
def showPosterInfo(poster_id):
    posterObj = Poster.query.get(poster_id)
    if posterObj is None:
        return "Something didn't work"
    else:
        return render_template('posterinfo.html', posterObj = posterObj)

@app.route('/<int:poster_id>/JSON')
def showPosterInfoJSON(poster_id):
    posterObj = Poster.query.get(poster_id)
    if posterObj is None:
        return "Something didn't work"
    else:
        return jsonify(Poster=[posterObj.serialize])

# page to display search results
@app.route('/searchResults/<string:category>/<int:id>')
def showSearchResults(category, id):
    # find all the posters for the given genre
    if category == 'genre':
        posters = Poster.query.filter_by(genre_id = id).all()
    elif category =='director':
        posters = Poster.query.filter_by(director_id = id).all()
    else:
        posters = Poster.query.filter_by(year = id).all()

    if len(posters) > 0:
        return render_template('searchResults.html', posters = posters)
    else:
        return "Nothing to see here"

# show years
# show page with genres
@app.route('/category/genre')
def showGenres():
    return render_template('genres.html', genres = genres)

@app.route('/category/genre/JSON')
def showGenresJSON():
    return jsonify(Genre=[i.serialize for i in genres])

# show page with genres
@app.route('/category/director')
def showDirectors():
    directors = Director.query.all()
    return render_template('directors.html', directors = directors)

@app.route('/category/director/JSON')
def showDirectorsJSON():
    directors = Director.query.all()
    return jsonify(Director=[i.serialize for i in directors])

@app.route('/category/year')
def showYears():
    uniqueYears = Poster.query.distinct(Poster.year).group_by(Poster.year)
    return render_template('years.html', years = uniqueYears)

@app.route('/category/year/JSON')
# todo - fix this mess
def showYearsJSON():
    uniqueYears = Poster.query.distinct(Poster.year).group_by(Poster.year)
    return jsonify(Poster=[i.serialize for i in uniqueYears])

# all the posters in a category
@app.route('/category/<int:category_id>')
def showPostersForCategory(category_id):
    return render_template('category.html', category_id = category_id)

# login page
@app.route('/login')
def login():
    return render_template('login.html')

if __name__  == '__main__':
    app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    app.run(host = '0.0.0.0', port=8000)
