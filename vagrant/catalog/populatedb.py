from dbmodel import db, Genre

# if we're starting with a blank database, we need to run this script to
# populate the genres

# create the genres
genres = [
    'Comedy',
    'Action',
    'Romance',
    'Western',
    'Sci-Fi',
    'Horror',
    'Musical',
    'Drama'
]

for genre in genres:
    db.session.add(Genre(name=genre))
    db.session.commit()