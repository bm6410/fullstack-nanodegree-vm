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
    return 'Edit poster with ID ' + str(poster_id) + ' here'

#delete poster page, protected behind login
#@auth.login_required
@app.route('/<int:poster_id>/delete')
def deletePoster(poster_id):
    return 'Delete poster with ID ' + str(poster_id) + ' here'

# info for a poster
@app.route('/<int:poster_id>')
def showPosterInfo(poster_id):
    return 'Show info for poster with ID ' + str(poster_id) + ' here'

# all the posters in a category
@app.route('/category/<int:category_id>')
def showPostersForCategory(category_id):
    return 'Show all the posters category with ID ' + str(category_id) + ' here'

# login page
@app.route('/login')
def login():
    return 'Login user here'

if __name__  == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port=8000)
