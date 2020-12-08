import pymongo
import datetime
import os
from dotenv import load_dotenv

## necessary for python-dotenv ##
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

mongo = os.getenv('MONGO')
client = pymongo.MongoClient(mongo)

db = client['bucket_list']

users = db['users']
roles = db['roles']
bucketList = db['bucketList']
categories = db['categories']
status = db['status']


def add_role(role_name):
    role_data = {
        'role_name': role_name
    }
    return roles.insert_one(role_data)





def add_user(first_name, last_name, username, email, password, role):
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'username' : username,
        'email': email,
        'password': password,
        'role': role,
        'date_added': datetime.datetime.now(),
        'date_modified': datetime.datetime.now()
    }
    return users.insert_one(user_data)


def add_activity(activity_name, category, description, share_status, estimated_cost, address, city, state, country, expected_date, username):
    activity_data = {
        'activity_name' : activity_name,
        'category' : category,
        'description' : description,
        'share_status' : share_status,
        'estimated_cost' : estimated_cost,
        'address' : address,
        'city' : city,
        'state' : state,
        'country' : country,
        'expected_date' : expected_date,
        
        'username' : username,

        'date_added': datetime.datetime.now(),
        'date_modified': datetime.datetime.now()
    }
    return bucketList.insert_one(activity_data)

def add_category(category_name):
    category_data = {
        'category_name': category_name
    }
    return categories.insert_one(category_data)

def add_status(share_status):
    status_data = {
        'share_status': share_status
    }
    return status.insert_one(status_data)

def initial_database():
    # add roles
    admin = add_role('admin')
    contributor = add_role('contributor')
    user = add_role('user')

    # add users
    marcus = add_user('Marcus', 'Porter', 'porter33marcus', 'marcus@porter.com', 'abc123', 'admin')

    # add category

    historic = add_category('Historic location')
    adrenaline = add_category('Adrenaline rush')
    nature = add_category('Nature')
    event = add_category('Event')
    

    # add status
    private = add_status('Private')
    public = add_status('Public')
   
    # add activity
    skydiving = add_activity('skydiving', 'Adrenaline rush','solo skydiving in colorado', 'Public', '$150', '1172 Airport Center Rd', 'Glenwood Springs', 'Colorado', 'United States of America', '06/15/2021', 'porter33marcus')

    

def main():
    initial_database()
   

main()
