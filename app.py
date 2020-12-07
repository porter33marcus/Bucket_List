import os
from dotenv import load_dotenv
import pymongo
import datetime
from bson.objectid import ObjectId
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
import bcrypt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

## necessary for python-dotenv ##
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

mongo = os.getenv('MONGO')

client = pymongo.MongoClient(mongo)

db = client['bucket_list'] # Mongo collection
users = db['users'] # Mongo document
roles = db['roles'] # Mongo document
categories = db['categories'] # Mongo document
bucketList = db['bucketList'] # Mongo document

login = LoginManager()
login.init_app(app)
login.login_view = 'login'

@login.user_loader
def load_user(username):
    u = users.find_one({"username": username})
    if not u:
        return None
    return User(username=u['username'], role=u['role'], id=u['_id'])

class User:
    def __init__(self, id, username, role):
        self._id = id
        self.username = username
        self.role = role

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username

'''
    @staticmethod
    def check_password(password_hash, password):
        return check_password_hash(password_hash, password)
'''

### custom wrap to determine role access  ### 
def roles_required(*role_names):
    def decorator(original_route):
        @wraps(original_route)
        def decorated_route(*args, **kwargs):
            if not current_user.is_authenticated:
                print('The user is not authenticated.')
                return redirect(url_for('login'))
            
            print(current_user.role)
            print(role_names)
            if not current_user.role in role_names:
                print('The user does not have this role.')
                return redirect(url_for('login'))
            else:
                print('The user is in this role.')
                return original_route(*args, **kwargs)
        return decorated_route
    return decorator


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/add-user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        form = request.form
        
        
        
        email = users.find_one({"email": request.form['email']})
        if email:
            flash('This email is already registered.', 'warning')
            return 'This email has already been registered.'
        new_user = {
            'first_name': form['first_name'],
            'last_name': form['last_name'],
            'username' : form['username'],
            'email': form['email'],
            'password': form['password'],
            'role': form['role'],
            'date_added': datetime.datetime.now(),
            'date_modified': datetime.datetime.now()
        }
        users.insert_one(new_user)
        flash(new_user['username'] + ' user has been added.', 'success')
        
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        user = users.find_one({"username": request.form['username']})
        if user and user['password'] == request.form['password']:
            user_obj = User(username=user['username'], role=user['role'], id=user['_id'])
            login_user(user_obj)
            next_page = request.args.get('next')

            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
                return redirect(next_page)
            flash("Logged in successfully!", category='success')
            return redirect(request.args.get("next") or url_for("index"))

        flash("Wrong username or password!", category='danger')
    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/my-account/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('user', 'contributor', 'admin')
def my_account(user_id):
    edit_account = users.find_one({'_id': ObjectId(user_id)})
    if edit_account:
        return render_template('my-account.html', user=edit_account)
    flash('User not found.', 'warning')
    return redirect(url_for('index'))

@app.route('/update-myaccount/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('user', 'contributor', 'admin')
def update_myaccount(user_id):
    if request.method == 'POST':
        form = request.form

        password = request.form['password']

        users.update({'_id': ObjectId(user_id)},
            {
            'first_name': form['first_name'],
            'last_name': form['last_name'],
            'username' : form['username'],
            'email': form['email'],
            'password': password,
            'role': form['role'],
            'date_added': form['date_added'],
            'date_modified': datetime.datetime.now()
            })
        update_account = users.find_one({'_id': ObjectId(user_id)})
        flash(update_account['email'] + ' has been updated.', 'success')
        return redirect(url_for('index'))
    return redirect(url_for('index'))


@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')

##########  Admin functionality -- User management ##########

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_users():
    return render_template('user-admin.html', all_roles=roles.find(), all_users=users.find())

@app.route('/admin/add-user', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_add_user():
    if request.method == 'POST':
        form = request.form
        
        password = request.form['password']
        
        email = users.find_one({"email": request.form['email']})
        if email:
            flash('This email is already registered.', 'warning')
            return 'This email has already been registered.'
        new_user = {
            'first_name': form['first_name'],
            'last_name': form['last_name'],
            'username' : form['username'],
            'email': form['email'],
            'password': password,
            'role': form['role'],
            'date_added': datetime.datetime.now(),
            'date_modified': datetime.datetime.now()
        }
        users.insert_one(new_user)
        flash(new_user['username'] + ' user has been added.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('user-admin.html', all_roles=roles.find(), all_users=users.find())

@app.route('/admin/delete-user/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_delete_user(user_id):
    delete_user = users.find_one({'_id': ObjectId(user_id)})
    if delete_user:
        users.delete_one(delete_user)
        flash(delete_user['username'] + ' has been deleted.', 'warning')
        return redirect(url_for('admin_users'))
    flash('User not found.', 'warning')
    return redirect(url_for('admin_users'))

@app.route('/admin/edit-user/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_edit_user(user_id):
    edit_user = users.find_one({'_id': ObjectId(user_id)})
    if edit_user:
        return render_template('edit-user.html', user=edit_user, all_roles=roles.find())
    flash('User not found.', 'warning')
    return redirect(url_for('admin_users'))

@app.route('/admin/update-user/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_update_user(user_id):
    if request.method == 'POST':
        form = request.form

        password = request.form['password']

        users.update({'_id': ObjectId(user_id)},
            {
            'first_name': form['first_name'],
            'last_name': form['last_name'],
            'username' : form['username'],
            'email': form['email'],
            'password': password,
            'role': form['role'],
            'date_added': form['date_added'],
            'date_modified': datetime.datetime.now()
            })
        update_user = users.find_one({'_id': ObjectId(user_id)})
        flash(update_user['username'] + ' has been updated.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('user-admin.html', all_roles=roles.find(), all_users=users.find())



@app.route('/activities/add-category', methods=['POST'])
@login_required
@roles_required('admin')
def add_category():
    if request.method == 'POST':
        form = request.form
        category = users.find_one({"category_name": request.form['new_category']})
        if category:
            flash('This category is already registered.', 'warning')
            return url_for('/admin_users')
        new_category = {
            'category_name': form['new_category'],
        }
        categories.insert_one(new_category)
        flash(new_category['category_name'] + ' has been added.', 'success')
        return redirect(url_for('admin_activities'))
    return render_template('activity-admin.html', all_categories=categories.find())

@app.route('/activities/delete_category/<category_id>', methods=['GET'])
@login_required
@roles_required('admin')
def delete_category(category_id):
    delete_category = categories.find_one({'_id': ObjectId(category_id)})
    if delete_category:
        categories.delete_one(delete_category)
        flash(delete_category['category_name'] + ' has been deleted.', 'danger')
        return redirect(url_for('admin_activities'))
    flash('activity not found.', 'warning')
    return redirect(url_for('admin_activities'))

    


##########  activities ##########
@app.route('/activities', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'contributor', 'user')
def view_activities():
    return render_template('activities.html', all_bucketList=bucketList.find())


@app.route('/activities/activities', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_activities():
    return render_template('activity-admin.html', all_categories=categories.find(), all_bucketList=bucketList.find())

@app.route('/activities/new-activity', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'contributor')
def activity_page():
    return render_template('new-activity.html', all_categories=categories.find(), all_bucketList=bucketList.find())




@app.route('/activities/add-activity', methods=['POST'])
@login_required
@roles_required('admin', 'contributor')
def add_activity():
    if request.method == 'POST':
        form = request.form
              
        new_activity = {
           
        'activity_name' : form['activity_name'],
        'category' : form['category'],
        'description' : form['description'],
        'estimated_cost' : form['estimated_cost'],
        'address' : form['address'],
        'city' : form['city'],
        'state' : form['state'],
        'country' : form['country'],
        'expected_date' : form['expected_date'],
        
        'username' : form['username'],

        'date_added': datetime.datetime.now(),
        'date_modified': datetime.datetime.now()
    
        }
        bucketList.insert_one(new_activity)
        flash('New activity has been added.', 'success')
        return redirect(url_for('view_activities'))
    return render_template('new-activity.html', all_categories=categories.find())

@app.route('/activities/edit-activity/<activity_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def edit_activity(activity_id):
    edit_activity = activities.find_one({'_id': ObjectId(activity_id)})
    if edit_activity:
        return render_template('edit-activity.html', activity=edit_activity, all_categories=categories.find())
    flash('activity not found.', 'danger')
    return redirect(url_for('admin_activities'))
@app.route('/activities/update-activity/<activity_id>', methods=['POST'])
@login_required
@roles_required('admin')
def update_activity(activity_id):
    if request.method == 'POST':
        form = request.form
        activities.update({'_id': ObjectId(activity_id)},
            {
                'activity_name' : form['activity_name'],
                'category' : form['category'],
                'description' : form['description'],
                'estimated_cost' : form['estimated_cost'],
                'address' : form['address'],
                'city' : form['city'],
                'state' : form['state'],
                'country' : form['country'],
                'expected_date' : form['expected_date'],
                
                'username' : form['username'],

                'date_added': form['date_added'],
                'date_modified': datetime.datetime.now()


           
            })
        update_activity = activities.find_one({'_id': ObjectId(activity_id)})
        flash(update_activity['activity_name'] + ' has been updated.', 'success')
        return redirect(url_for('view_activities'))
    return render_template('edit-activity.html', all_categories=categories.find())


@app.route('/activities/delete-activity/<activity_id>', methods=['POST'])
@login_required
@roles_required('admin')
def delete_activity(activity_id):
    delete_activity = activities.find_one({'_id': ObjectId(activity_id)})
    if delete_activity:
        activities.delete_one(delete_activity)
        flash(delete_activity['activity_name'] + ' has been deleted.', 'danger')
        return redirect(url_for('view_activities'))
    flash('activity not found.', 'warning')
    return redirect(url_for('view_activities'))
# authenticated users can print a activity
@app.route('/activities/print-activity/<activity_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'contributor', 'user')
def print_activity(activity_id):
    print_activity = bucketList.find_one({'_id': ObjectId(activity_id)})
    if print_activity:
        return render_template('print-activity.html', activity=print_activity)
    flash('activity not found.', 'danger')
    return redirect(url_for('view_activities'))


if __name__ == "__main__":
    app.run(debug=True)