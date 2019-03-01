# Stick and Burn Poster Catalog

This project is my attempt at completing the Item Catalog Project.  The application presents a catalog of movie posters, searchable by Year, Genre, and Director.

Anyone can browse the catalog, but add/edit/delete functions are limited to those who log into the
app via Google Accounts.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 

Download the code from github:  https://github.com/bm6410/fullstack-nanodegree-vm

The project lives in the "catalog" directory

### Prerequisites

Requirements for running the code are found in requirements.txt.

```
    pip  install  -r  requirements.txt
```

### Installing
Installation has a couple options:

**1. Install with a pre-populated database**

For this option, please use the posters.db file included in the project. This file includes contains several poster records across various genres, etc.

**2. Install with a blank database**

For this option, remove posters.db from the directory.

Running dbmodel.py will instantiate a blank posters.db file:
```
python dbmodel.py
```

Running populatedb.py populate the predefined genres:
```
python populatedb.py
```

After the database has been created, then simply run the following:

```
python application.py
```

### Usage


The application is configured to run on port 8000.

To launch the app, open the root in your browser (localhost:8000).


## Built With

* [Flask](http://flask.pocoo.org/) - The web framework used
* [SQLAlchemy](https://www.sqlalchemy.org/) - Sql toolkit and ORM
* [Python](https://www.python.org/) - Server code

## Authors

* **Bijan Marashi** - [bm6410](https://github.com/bm6410)

## Acknowledgments

* Thanks to Udacity for various bits of sample code
* Hero image photographed by Rob Laughter
* Thanks to [PurpleBooth](https://gist.github.com/PurpleBooth) for the README.md template

