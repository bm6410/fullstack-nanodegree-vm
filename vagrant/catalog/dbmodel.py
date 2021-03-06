from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import random
import string
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from itsdangerous import(
    TimedJSONWebSignatureSerializer as
    Serializer,
    BadSignature,
    SignatureExpired
)

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posters.db'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://bijan:myHanh1974@127.0.0.1/posters'
# aws db string
# app.config['SQLALCHEMY_DATABASE_URI'] =
# 'postgresql://postgres@127.0.0.1/posters'
# heroku db string
# app.config['SQLALCHEMY_DATABASE_URI'] =
# 'postgres://wdsqrknzpwvcjx:dfb9661f6d407f1b5eb42fef5f9ca867da71d3303855a2f1e41652a7df67d396@ec2-50-19-109-120.compute-1.amazonaws.com:5432/db3p8pc80o93lj'
db = SQLAlchemy(app)

# Random key used to sign tokens
secret_key = \
    ''.join(random.choice(string.ascii_uppercase + string.digits)
            for x in range(32))


# class to store user/password info.  Borrowed from Udacity example code
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    picture = db.Column(db.String)
    email = db.Column(db.String)
    # token = db.Column(db.Text)
#    password_hash = db.Column(db.String(64))

    # def hash_password(self, password):
    #     self.password_hash = pwd_context.encrypt(password)
    #
    # def verify_password(self, password):
    #     return pwd_context.verify(password, self.password_hash)

    # Generate auth tokens - didn't end up using this
    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id})

    # Verify auth tokens here
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            # Valid token, but expired
            return None
        except BadSignature:
            # Invalid token
            return None
        user_id = data['id']
        return user_id

    @property
    def serialize(self):
        return {
            'id': self.id,
            'username': self.name,
            'picture': self.picture,
            'email': self.email
        }


# Directors
class Director(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }


# Genres
class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }


# A Poster object
class Poster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    genre_id = db.Column(db.Integer, ForeignKey("genre.id"))
    genre = relationship(Genre)
    director_id = db.Column(db.Integer, ForeignKey("director.id"))
    director = relationship(Director)
    year = db.Column(db.String)
    poster_img = db.Column(db.String)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'title': self.title,
            'genre_id': self.genre_id,
            'genre': self.genre.name,
            'director_id': self.director_id,
            'director': self.director.name,
            'year': self.year,
            'poster_img': self.poster_img,
            'user_id': self.user_id,
            'user_name': self.user.username
            }


db.create_all()
