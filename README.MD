#Catalog Web-App

##About
This app can be used to set-up a database and website to serve up a catalog web
app. The website provides a RESTFUL API and full CRUD operations to store items
that are divided into different categories. A JSON endpoint is provided to return
all items in the database in easy to parse JSON format. An ATOM Feed is provided
to return a list of the most recently added items. User authorization is provided
by google's OAUTH2 system.

##How to run

###Set up the database
1. The **database_setup.py** file is used to create the database. Navigate to the root
directory of the app on the command line and run: `python database_setup.py`
2. Optionally, the **lotsofitems.py** file can be used to populate the database with sample
items. To run, from the command line run: `python lotsofitems.py`

###Run Web App
1. First you need to fire up the web server to serve the site. From the command line,
   navigate to the root of the app (same location as in the database setup step) and
   run: `python application.py`
   * This will run the site on your local machine on port 8000
2. In your favourite web browser, navigate to `localhost:8000` to access the app.

###Navigate Site
On all pages, clicking the page title in the banner will redirect the site to the home page.
On normal user pages (ie. not including admin pages or login page) you will find:
* On the left you will see a list of categories. Clicking a category will navigate
  to that category's page
* Below the list of categories you will find the 'Login' button (if not already logged
  in). Click to go to the login page.
* If you are already logged in, below the list of categories you will see a 'Logout'
  button, and an 'Add Item' button. The 'Logout' button can be clicked to log out the user,
  while the 'Add Item' button is used to navigate to the add item form.

####Front Page (`/` or `catalog/`)
  * The front page displays the last 7 items added to the catalog in descending order.
  * Clicking anywhere on the item preview will navigate to the item's main page.

####Category Page (`catalog/<category_name>/`)
  * The category page displays all of the items in that particular category.
  * Clicking anywhere on the item preview will navigate to the item's main page.

####Item Page (`catalog/<category_name>/<item_id>/`)
  * The item page displays info for a particular item, including an image, a description,
    and a price.
  * Depending on the availability of stock, you will see a message stating the item is in stock,
    limited number available, or out of stock.
  * If the user is logged in, they will see an 'Edit Item' button and a 'Delete Item' button. The
    'Edit Item' button directs the user to a form where they can edit the details of the item.
    The 'Delete Item' button directs the user to a confirmation page.

###Loginng In and Out
1. From the login page (`login/`), the user has the option to login using their Google account. Just
   click the 'g+ Sign In' button and then click 'Accept' on the Google confirmation pop-up.
2. After a few moments, if login was successful, you will see a confirmation message with your name and
   Google profile picture, before the browser automatically redirects to the front page.
3. In order to log back out, just hit the 'Logout' button in the left side-bar. After successfully
   logging out, the browser will automatically redirect to the front page.

###CRUD Operations
User must be logged in to perform any of the following CRUD operations.

####Create (Add Item)
1. Click the 'Add Item' button on the left side bar, or navigate to `admin/additem/`
2. Enter item details.
  * Name, price, and category are required. The form will not submit if they are blank.
  * Description will default to a blank string if user does not enter a description.
  * Number available will default to 0 if no number is entered. The input field will only
    accept numbers greater than or equal to 0.
  * If image is left blank, a default 'no-image' image will be displayed when later viewing
    the item.
  * If an image is selected, you will see a thumbnail preview of that image.
  * Price must be in the format of valid Canadian or US currency. Commas can optionally be used
    for thousands, millions, etc. If cents are specified, two decimal places are required.
  * In category, a pull down list of existing categories are available. The user can select one
    of these categories, or type in a new category name. It the latter case, a new category will
    be created and stored in the database. This category will subsequently appear in the category
    list in the left side-bar.
  * Click submit. The form will be submitted, the item will be created and stored in the database
    (along with a new category if necessary). If an image was selected, it will be uploaded to the
    uploads folder.
  * The browser will redirect to the front page.

####Update Item
1. Navigate to the item you wish to update, then click the 'Edit Item' button near the bottom
   of the page. If you know the id of the item you wish to update, you can manually access the
   update page at `admin/<item_id>/edit/`.
2. Current values for each field will be pre-populated in the form. Edit the items that need to be
   changed.
  * The form acts exactly the same as the add item form.
  * Upon submission, if the image was changed, the previous image will be deleted from the uploads
    folder.
  * After submission has completed, the user will be redirected to the item's page.

####Delete Item
1. Navigate to the item you wish to delete, then click the 'Delete Item' button near the bottom of the
  page.
2. From the confirmation screen, click 'Delete Item' to delete the item.
  * If you change your mind, you can click the 'Cancel' button to navigate back to the item's page
  * Clicking delete will remove the item from the database. If the item had an image, the image will
    be deleted from the uploads directory.
  * A nonce value is used to protect from cross-site forgery attacks.
  * After successfully deleting an item, the browser will redirect to the front page.

###JSON Endpoint
A JSON file containing all of the items in the database in each category is available at `catalog.json`
from the root directory.

###ATOM Feed
An ATOM feed containing the most recently added items can be found at `recent_items.atom` from the root
directory.
