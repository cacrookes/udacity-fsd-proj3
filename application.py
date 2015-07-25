import os, json, collections, random, string, httplib2, requests
#import json
#import collections
#import random, string
from urlparse import urljoin
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, make_response
from flask import flash, session as login_session
from werkzeug.contrib.atom import AtomFeed
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "FSD Catalog App"

# Connect to Database and create database session
engine = create_engine('sqlite:///hockeyshop.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# checks to see if a category already exists. If not, category is added. Returns category id
def categoryCheck(category_name):
    if session.query(Category).filter_by(name=category_name).count():
        # category already exists
        return session.query(Category).filter_by(name=category_name).one().id
    else:
        # new category
        newCategory = Category(name=category_name)
        session.add(newCategory)
        session.commit()

        # get id of new category
        return session.query(Category).filter_by(name=category_name).one().id

# create an absolute url for external services.
def external_url(url):
    return urljoin(request.url_root, url)

# JSON endpoint to serve JSON data
@app.route('/catalog.json')
def catalogJSON():
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

# Atom Feed to return list of the most recently added items
@app.route('/recent_items.atom')
def atom_feed():
    feed = AtomFeed('Newest Items at The Hockey Shop', feed_url=request.url, url=request.url_root)
    items = session.query(Item).order_by(Item.date_added.desc()).limit(20).all()
    for item in items:
        feed.add(item.name,
                 item.description,
                 content_type='text',
                 url=external_url(url_for('showItem',category_name=item.category.name, item_id=item.id)),
                 updated=item.date_added)
    return feed.get_response()

# Create a state token to prevent request forgery.
# Store it in the session for later validation
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
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
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# Home page, listing newest items and categories for navigation
@app.route('/catalog/')
@app.route('/')
def mainPage():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.date_added.desc()).limit(7)
    return render_template('main.html', categories=categories, items=items)

# List all the items available in the category
@app.route('/catalog/<category_name>/')
def showCategory(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id = category.id).all()
    categories = session.query(Category).all()
    return render_template('category.html', items=items, category=category_name, categories=categories)

# List details for given item
@app.route('/catalog/<category_name>/<int:item_id>/')
def showItem(category_name, item_id):
    item = session.query(Item).filter_by(id = item_id).one()
    categories = session.query(Category).all()
    return render_template('item.html', item=item, categories=categories)

# Form for adding a new item
@app.route('/admin/additem/', methods=['GET', 'POST'])
def newItem():
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
            image.save(os.path.join('uploads/', image_name))

        newItem = Item( name=request.form['name'],
                        description=request.form['description'],
                        price=cents,
                        num_avail=request.form['numAvail'],
                        image=image_name,
                        category_id=category_id)

        session.add(newItem)
        session.commit()
        return redirect(url_for('mainPage'))
    else:
        categories = session.query(Category).all()
        return render_template('addItem.html', categories=categories)

# Form for updating the specified item
@app.route('/admin/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':

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
            # Check if category exists. If not, add it to the database. Get category id.
            editedItem.category_id = categoryCheck(request.form['category'])

        # Upload the image and get filename
        image = request.files['image']
        if image:
            image_name = image.filename
            #check if image has changed
            if editedItem.image != image_name:
                # delete old file if it exists
                if editedItem.image != "":
                    os.remove(os.path.join('uploads/', editedItem.image))
                image.save(os.path.join('uploads/', image_name))
                editedItem.image = image_name

        session.add(editedItem)
        session.commit()
        return redirect(url_for('mainPage'))
    else:
        categories = session.query(Category).all()
        return render_template('editItem.html', item=editedItem, categories=categories)

# Confirmation page for deleting a specified item
@app.route('/admin/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(item_id):
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        # if item had image, delete image from server
        if itemToDelete.image != "":
            os.remove(os.path.join('uploads/', itemToDelete.image))
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('mainPage'))
    else:
        return render_template('deleteItem.html', item=itemToDelete)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads/', filename)

if __name__ == '__main__':
        app.secret_key = '#ufD\x93K\x05\xf2\xd5\x02\xf4\xdbw[R\x10\xbcRR\x8a\xd9\xd6\x80p'
        app.debug = True
        app.run(host = '0.0.0.0', port = 8000)
