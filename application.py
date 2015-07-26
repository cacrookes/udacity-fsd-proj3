import os, json, collections, random, string, httplib2, requests
from urlparse import urljoin
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, make_response
from flask import flash, session as login_session
from werkzeug.contrib.atom import AtomFeed
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from datetime import datetime, timedelta

app = Flask(__name__)

#---------------------------------------------------------------------------
# This app provides routing and serves up a website catalog app with full
# CRUD operations and a RESTFUL API
#---------------------------------------------------------------------------

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "FSD Catalog App"
# set the folder where item images will be uploaded to
UPLOADS_FOLDER = "uploads/"

# Connect to Database and create database session
engine = create_engine('sqlite:///hockeyshop.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def categoryCheck(category_name):
    """
    Checks to see if a category already exists.
    If not, category is added. Returns category id.
    """
    if session.query(Category).filter_by(name=category_name).count():
        # category already exists
        return session.query(Category).filter_by(name=category_name).one().id
    else:
        # new category
        newCategory = Category(name=category_name)
        session.add(newCategory)
        session.commit()

        flash("Category %s created" % category_name)
        # get id of new category
        return session.query(Category).filter_by(name=category_name).one().id

def deleteEmptyCategory(category_id):
    """
    Checks to see if a category has any items in it.
    If not, category is deleted
    """
    print "In delete empty category"
    # following will return None if no results are found
    categoryItems = session.query(Item).filter_by(category_id=category_id).first()
    if not categoryItems:
        # no items in this category, so delete it!
        categoryToDelete = session.query(Category).filter_by(id=category_id).one()
        session.delete(categoryToDelete)
        session.commit()
        flash("Category %s was removed" % categoryToDelete.name)
        return "Category deleted"
    else:
        # category still has items
        return "Category was not deleted. It still contains items."

def external_url(url):
    """
    Creates an absolute url for external services.
    """
    return urljoin(request.url_root, url)

@app.route('/catalog.json')
def catalogJSON():
    """
    JSON endpoint to serve JSON data
    """
    categories = []
    category_objects = session.query(Category).all()
    # go through each category, and build an object for each category, including
    # an object representing all items in the category
    for c in category_objects:
        items = session.query(Item).filter_by(category_id = c.id).all()
        category = collections.OrderedDict()
        category['id'] = c.id
        category['name'] = c.name
        # assign serialized list of all items belong to category to 'item' property
        category['item'] = [i.serialize for i in items]
        categories.append(category)
    catalog = {
        'Category': categories
    }
    return jsonify(catalog)


@app.route('/recent_items.atom')
def atom_feed():
    """
    Atom Feed to return list of the most recently added items
    """
    feed = AtomFeed('Newest Items at The Hockey Shop', feed_url=request.url, url=request.url_root)
    items = session.query(Item).order_by(Item.date_added.desc()).limit(20).all()
    for item in items:
        feed.add(item.name,
                 item.description,
                 content_type='text',
                 url=external_url(url_for('showItem',category_name=item.category.name, item_id=item.id)),
                 updated=item.date_added)
    return feed.get_response()

@app.route('/login')
def showLogin():
    """
    Create a state token to prevent request forgery.
    Store it in the session for later validation
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Connect to the google oauth2 service for user authentication
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
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

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    # Grab the current time and length of time for the access token to determine when it expires
    login_session['logintime'] = datetime.now()
    login_session['access_length'] = credentials.token_response["expires_in"]

    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # store user data in session for later retrieval
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Generate html for welcome message to display on successful login
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    return output


def logoutCleanup():
    """
    handles clean-up from logging out user
    """
    # Reset the user's sesson.
    del login_session['credentials']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['logintime']
    del login_session['access_length']

    flash("You have been successfully disconnected.")
    return redirect(url_for('mainPage'))

@app.route('/gdisconnect')
def gdisconnect():
    """
    Revoke a current user's Google oauth2 token and resets their login_session
    """
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % credentials
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        return logoutCleanup()
    else:
        # Check to see if the access token has expired. This would cause an error when
        # trying to revoke it since its already revoked. In this case, we can safely logout
        # the user.
        if (datetime.now() - login_session['logintime']) > timedelta(seconds=login_session['access_length']):
            return logoutCleanup()

        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/catalog/')
@app.route('/')
def mainPage():
    """
    Home page, listing newest items and categories for navigation
    """
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.date_added.desc()).limit(7)
    return render_template('main.html', categories=categories, items=items)

@app.route('/catalog/<category_name>/')
def showCategory(category_name):
    """
    List all the items available in the category
    """
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id = category.id).all()
    categories = session.query(Category).all()
    return render_template('category.html', items=items, category=category_name, categories=categories)

@app.route('/catalog/<category_name>/<int:item_id>/')
def showItem(category_name, item_id):
    """
    List details for given item
    """
    item = session.query(Item).filter_by(id = item_id).one()
    categories = session.query(Category).all()
    return render_template('item.html', item=item, categories=categories)

@app.route('/admin/additem/', methods=['GET', 'POST'])
def newItem():
    """
    Form for adding a new item
    """
    # Check to make sure user is authorized to add item
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        # Check if category exists. If not, add it to the database. Get category id.
        category_id = categoryCheck(request.form['category'])

        # Convert price from dollars to cents. Database stores price as integer instead
        # of decimal due to compiler warnings of lack of native decimal support
        cents = float(request.form['price']) * 100

        # Upload the image and get filename
        image = request.files['image']
        image_name = ""
        if image:
            image_name = image.filename
            image.save(os.path.join(UPLOADS_FOLDER, image_name))

        newItem = Item( name=request.form['name'],
                        description=request.form['description'],
                        price=cents,
                        num_avail=request.form['numAvail'],
                        image=image_name,
                        category_id=category_id)

        session.add(newItem)
        session.commit()
        flash("Succesfully added %s" % newItem.name)
        return redirect(url_for('mainPage'))
    else:
        categories = session.query(Category).all()
        return render_template('addItem.html', categories=categories)

@app.route('/admin/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(item_id):
    """
    Form for updating the specified item
    """
    # Check to make sure user is authorized to edit item
    if 'username' not in login_session:
        return redirect('login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        # cat_changed will store if category of item has changed or not.
        cat_changed = False
        old_cat_id = editedItem.category_id
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            # Convert price from dollars to cents. Database stores price as integer instead
            # of decimal due to compiler warnings of lack of native decimal support
            editedItem.price = float(request.form['price']) * 100
        if request.form['numAvail']:
            editedItem.num_avail = request.form['numAvail']
        if request.form['category']:
            # if the item's category was changed, make note.
            # After we update the item, we will check if the old category still has items
            # in it. If not, remove the category.
            if editedItem.category.name != request.form['category']:
                cat_changed = True
            # Check if new category exists. If not, add it to the database. Get category id.
            editedItem.category_id = categoryCheck(request.form['category'])

        # Upload the image and get filename
        image = request.files['image']
        if image:
            image_name = image.filename
            #check if image has changed
            if editedItem.image != image_name:
                # delete old file if it exists
                if editedItem.image != "":
                    os.remove(os.path.join(UPLOADS_FOLDER, editedItem.image))
                image.save(os.path.join(UPLOADS_FOLDER, image_name))
                editedItem.image = image_name

        session.add(editedItem)
        session.commit()
        # if the category was changed, check if old category still has items in it.
        # if not, delete the category
        if cat_changed:
            deleteEmptyCategory(old_cat_id)

        flash("Successfully updated %s" % editedItem.name)
        return redirect(url_for('showItem', category_name=editedItem.category.name, item_id=item_id))
    else:
        categories = session.query(Category).all()
        return render_template('editItem.html', item=editedItem, categories=categories)

@app.route('/admin/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(item_id):
    """
    Confirmation page for deleting a specified item
    """
    # Check to make sure user is authorized to delete item
    if 'username' not in login_session:
        return redirect('login')
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        # verify nonce to help prevent cross-site request forgeries
        if request.form["nonce"] != login_session["nonce"]:
            flash("Error, could not delete %s" %itemToDelete.name)
            return redirect(url_for('mainPage'))
        del login_session["nonce"]
        # if item had image, delete image from server
        if itemToDelete.image != "":
            os.remove(os.path.join(UPLOADS_FOLDER, itemToDelete.image))
        session.delete(itemToDelete)
        session.commit()
        # Check to see if the deleted item's category contains other items.
        # If not, delete the category.
        deleteEmptyCategory(itemToDelete.category_id)
        flash("Successfully delete %s" % itemToDelete.name)
        return redirect(url_for('mainPage'))
    else:
        # create nonce to help protect from cross-site request forgeries
        login_session["nonce"] = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        return render_template('deleteItem.html', item=itemToDelete, nonce=login_session["nonce"])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Returns url for a file in the uploads folder
    """
    return send_from_directory('uploads/', filename)

if __name__ == '__main__':
        app.secret_key = '#ufD\x93K\x05\xf2\xd5\x02\xf4\xdbw[R\x10\xbcRR\x8a\xd9\xd6\x80p'
        app.debug = True
        app.run(host = '0.0.0.0', port = 8000)
