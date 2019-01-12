from flask import Flask, render_template
app = Flask(__name__)


# home page
@app.route('/')
def showHomePage():
    return render_template('index.html')

# new poster page, protected behind login
@app.route('/new')
#@auth.login_required
def addNewPoster():
    return render_template('newposter.html')

# edit poster page, protected behind login
#@auth.login_required
@app.route('/<int:poster_id>/edit')
def editPoster(poster_id):
    return render_template('editPoster.html')

#delete poster page, protected behind login
#@auth.login_required
@app.route('/<int:poster_id>/delete')
def deletePoster(poster_id):
    return render_template('deletePoster.html')

# info for a poster
@app.route('/<int:poster_id>')
def showPosterInfo(poster_id):
    return render_template('posterinfo.html')

# all the posters in a category
@app.route('/category/<int:category_id>')
def showPostersForCategory(category_id):
    return render_template('category.html')

# login page
@app.route('/login')
def login():
    return render_template('login.html')

if __name__  == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port=8000)
