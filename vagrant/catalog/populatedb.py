from dbmodel import db, Genre

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
