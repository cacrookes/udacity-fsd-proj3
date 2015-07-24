from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category

app = Flask(__name__)

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


# Home page, listing newest items and categories for navigation
@app.route('/')
def mainPage():
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return render_template('main.html', categories=categories, items=items)

# List all the items available in the category
@app.route('/<category_name>/')
def showCategory(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id = category.id).all()
    categories = session.query(Category).all()
    return render_template('category.html', items=items, category=category_name, categories=categories)

# List details for given item
@app.route('/<category_name>/<int:item_id>/')
def showItem(category_name, item_id):
    item = session.query(Item).filter_by(id = item_id).one()
    categories = session.query(Category).all()
    return render_template('item.html', item=item, categories=categories)

# Form for adding a new item
@app.route('/additem/', methods=['GET', 'POST'])
def newItem():
    if request.method == 'POST':
        # Check if category exists. If not, add it to the database. Get category id.
        category_id = categoryCheck(request.form['category'])

        # Convert price from dollars to cents. Database stores price as integer instead
        # of decimal due to compiler warnings of lack of native decimal support
        cents = float(request.form['price']) * 100
        newItem = Item( name=request.form['name'],
                        description=request.form['description'],
                        price=cents,
                        num_avail=request.form['numAvail'],
                        category_id=category_id)
        #TODO: add image logic
        session.add(newItem)
        session.commit()
        return redirect(url_for('mainPage'))
    else:
        categories = session.query(Category).all()
        return render_template('addItem.html', categories=categories)

# Form for updating the specified item
@app.route('/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        #TODO: check if category exists. If not, add it to the database
        #TODO: update editItem with values from form
        session.add(editedItem)
        session.commit()
        return redirect(url_for('mainPage'))
    else:
        return render_template('editItem.html', item=editedItem)

# Confirmation page for deleting a specified item
@app.route('/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(item_id):
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('mainPage'))
    else:
        return render_template('deleteItem.html', item=itemToDelete)


if __name__ == '__main__':
        app.debug = True
        app.run(host = '0.0.0.0', port = 8000)
