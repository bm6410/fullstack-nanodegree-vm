#**Stick and Burn Poster Catalog**
### by Bijan Marashi (bm6410@att.com)
#### February 22, 2019

This project is my attempt at completing the Item Catalog Project.


###**Installation**

Download the code from github:  https://github.com/bm6410/fullstack-nanodegree-vm

The project lives in the catalog directory

The application relies on Flask and SQLAlchemy.  In addition to the standard libraries, the code
relies on the following packages:

    * werkzeug.utils - file system tools
    * werkzeug.exceptions - for help with uploading poster images
    * PIL - for Image manipulation support


#####Installation has a couple options:
1) Install with a pre-populated database

    For this option, please use the posters.db file included in the project.  This file includes 
    contains several poster records across various genres, etc.
    
2) Install with a blank database

    For this option, remove posters.db from the directory, and run the following python commands:
    * python dbmodel.py
    * python populatedb.py
    
    This will instantiate a blank posters.db file, then populate the predefined genres.
    
After the database has been created, then simply run the following:
    * python application.py

###**Usage**


The application is configured to run on port 8000.

To launch the app, open the root in your browser (localhost:8080).  

The application presents a catalog of movie posters, searchable by Year, Genre, and Director.

Anyone can browse the catalog, but add/edit/delete functions are limited to those who log into the
app via Google Accounts

###**Sources**

This application uses code borrowed from Udacity's Full Stack Web Developer course examples.  Some
code snippets come from the Flask and SQLAlchemy knowledge bases, as well.

##**HAVE FUN!**