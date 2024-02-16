# Flask Application
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import pandas as pd
from datetime import datetime, timedelta
from bson import ObjectId
import time

app = Flask(__name__)
app.secret_key = "hofho433496jda@afhd"

# MongoDB configuration
client = MongoClient('mongodb://localhost:27017/')
db = client['net_calorie_tracker']
user_collection = db['users']
food_data_t = db["food_data"]
activities_data_t = db["activities_data"]

food_data = pd.DataFrame(list(food_data_t.find()))
activities_data = pd.DataFrame(list(activities_data_t.find()))
users = pd.DataFrame(list(user_collection.find()))

# Extract required columns
food_options = food_data.to_dict(orient='records')  # Convert DataFrame to list of dictionaries
activity_options = activities_data['ACTIVITY'].unique().tolist()
activities = activity_options

# Routes

@app.route('/')
def home():
    return render_template('home.html', food_options=food_options, activity_options=activity_options, activities = activities)
def index():
    today = datetime.today().strftime('%Y-%m-%d')
    thirty_days_ago = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    return render_template('form.html', today=today, thirty_days_ago=thirty_days_ago, tomorrow=tomorrow)

@app.route('/specific_motions/<activity>')
def specific_motions(activity):
    specific_motions = activities_data[activities_data['ACTIVITY'] == activity]['SPECIFIC MOTION'].unique().tolist()
    return {'specific_motions': specific_motions}

@app.route('/mets/<activity>')
def met(activity):
    mets = activities_data[activities_data['SPECIFIC MOTION'] == activity]['METs'].tolist()
    return {'met': mets}

@app.route('/form', methods=['GET', 'POST'])
def form():
    uid = request.args.get('UID')
    user_info = None
    if uid:
        user_info = user_collection.find_one({'UID': int(uid)})
    print("Activities:", activities)
    return render_template('form.html', food_options=food_options, activity_options=activity_options, activities=activities, user_info=user_info)
@app.route('/users')
def users():
    # Fetch all users
    users_data = list(user_collection.find())
    # Convert to DataFrame
    users_df = pd.DataFrame(users_data)
    # Extract unique user IDs
    unique_user_ids = users_df['UID'].unique()
    # Initialize list to store unique user details
    unique_user_list = []
    # Iterate over unique user IDs
    for uid in unique_user_ids:
        # Find the first occurrence of user with current UID
        user = users_df.loc[users_df['UID'] == uid].iloc[0].to_dict()
        # Append user details to unique_user_list
        unique_user_list.append(user)
    return render_template('users.html', user_list=unique_user_list)

@app.route('/edit_user/<_id>')
def edit_user(_id):
    _id = ObjectId(_id)
    user_t = pd.DataFrame(list(user_collection.find({'_id': _id})))
    res = user_t.to_dict(orient='records')
    # Logic to handle viewing user with user_id
    return render_template('edit_user.html', _id=_id, res=res, food_options=food_options, activity_options=activity_options, activities = activities)


@app.route('/view_user/<_id>', methods=['GET', 'POST'])
def view_user(_id):
    _id = ObjectId(_id)
    user_datat = user_collection.find_one({'_id': _id})
    print(user_datat)

    if user_datat:
        # Extract UID from user_data
        UIDx = user_datat.get('UID')
        user_data_t = pd.DataFrame(list(user_collection.find({'UID': UIDx})))
        user_data = user_data_t.to_dict(orient='records')
        filtered_list_of_dicts = [{key: d[key] for key in ['sex','duration','met','age','weight','height','food', 'calories', 'daytimeselect']} for d in user_data]
        food_list = pd.DataFrame(filtered_list_of_dicts)
        if request.method == 'POST':
            date = request.form.get('date_input')
            food_list['daytimeselect'] = pd.to_datetime(food_list['daytimeselect'])
            food_list = food_list[food_list['daytimeselect'] == date]
        food_list['calories'] = pd.to_numeric(food_list['calories'], errors='coerce')
        hrd = (food_list['duration'])/60
        food_list['met_duration'] = food_list['met'] * hrd
        sum_met_duration = food_list['met_duration'].sum()
        sum_calories = food_list['calories'].sum()
        sex1 = user_data[0]['sex']
        print(user_data)
        wt_avg = food_list['weight'].mean()
        ht_avg = food_list['height'].mean()
        age_avg = food_list['age'].max()
        food_list = food_list.to_dict('records')
        if sex1 == 'male':
            bmr = 664.730 + (13.7516 * wt_avg) + (5.0033 * ht_avg) - (6.7550 * age_avg)
        else:
            bmr = 655.0955 + (9.5634 * wt_avg) + (1.8496 * ht_avg) - (4.6756 * age_avg)

        total_calories_out = sum_met_duration * wt_avg
        NCD = sum_calories - bmr - total_calories_out
        print(f"DEBUG: Total calories out: {total_calories_out}")

        return render_template('view_user.html', res=user_data, bmr=bmr, total_calories_out=total_calories_out, NCD =NCD, fl = food_list, sc = sum_calories)

    else:
        flash('User Data Not Found')
        return redirect(url_for('users'))

@app.route('/delete_user/<_id>')
def delete_user(_id):
    try:
        _id = ObjectId(_id)
        result = user_collection.delete_one({'_id': _id})
        if result.deleted_count == 1:
            print("Data is deleted")
            time.sleep(5)
            return redirect(url_for('home'))
        else:
            print(f"No user found with _id {_id}. Nothing was deleted")
            time.sleep(5)
            return redirect(url_for('home'))

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        time.sleep(5)
        return redirect(url_for('home'))

@app.route('/select_user', methods=['POST'])
def select_user():
    user_id = request.form['_id']
    # Fetch user data for the selected user_id from MongoDB
    user_data = user_collection.find_one({'_id': ObjectId(user_id)})
    return render_template('form.html', user=user_data)

@app.route('/submit', methods=['POST'])
def submit_form():
    # Get form data from request
    motion_met_dict = dict(zip(activities_data['SPECIFIC MOTION'], activities_data['METs']))

    # Extract form data
    UID = int(request.form['UID'])
    name = request.form['name']
    age = int(request.form['age'])
    weight = float(request.form['weight'])
    height = float(request.form['height'])
    gender = request.form['sex']
    food = request.form['food']
    meal = request.form['meal']
    no_servings = int(request.form['no_servings'])
    calories = float(request.form['calories'])
    activity_select = request.form.get('activity_select')
    specific_motion_select = request.form.get('specific_motion_select')
    met = motion_met_dict.get(specific_motion_select)
    duration = float(request.form.get('duration'))
    daytimeselect = request.form.get('date_input')
    if gender == "male":
        bmr = 664.730 + (13.7516 * weight) + (5.0033 * height) - (6.7550 * age)
    elif gender == "female":
        bmr = 665.095 + (9.5634 * weight) + (1.84963 * height) - (4.6756 * age)
    else:
        bmr = 0  # Handle other cases as needed
    # Check if UID already exists
    existing_user = user_collection.find_one({'UID': UID})
    if existing_user:
        # If UID exists, verify that the name and gender match
        if existing_user['name'] != name or existing_user['sex'] != gender:
            flash('Please Change UID. Name and gender do not match existing record.', 'error')
            return redirect(url_for('form'))

    # Construct user_info dictionary
    user_info = {
        'UID': UID,
        'name': name,
        'age': age,
        'weight': weight,
        'height': height,
        'sex': gender,
        'food': food,
        'meal': meal,
        'no_servings': no_servings,
        'calories': calories,
        'activity_select': activity_select,
        'specific_motion_select': specific_motion_select,
        'met': met,
        'duration': duration,
        'daytimeselect': daytimeselect,
        'bmr': bmr  # Include calculated BMR
    }
    # Insert user_info into MongoDB collection
    user_collection.insert_one(user_info)

    # Redirect to the form route (or wherever you want)
    return redirect(url_for('form'))

@app.route('/submit_rep', methods=['POST'])
def edit_sub_form():
    # Get form data from request
    motion_met_dict = dict(zip(activities_data['SPECIFIC MOTION'], activities_data['METs']))

    # Extract form data
    _id = ObjectId(request.form['_id'])
    UID = int(request.form['UID'])
    name = request.form['name']
    age = int(request.form['age'])
    weight = float(request.form['weight'])
    height = float(request.form['height'])
    gender = request.form['sex']
    food = request.form['food']
    meal = request.form['meal']
    no_servings = int(request.form['no_servings'])
    calories = float(request.form['calories'])
    activity_select = request.form.get('activity_select')
    specific_motion_select = request.form.get('specific_motion_select')
    met = motion_met_dict.get(specific_motion_select)
    duration = float(request.form.get('duration'))
    daytimeselect = request.form.get('date_input')

    if gender == "male":
        bmr = 664.730 + (13.7516 * weight) + (5.0033 * height) - (6.7550 * age)
    elif gender == "female":
        bmr = 665.095 + (9.5634 * weight) + (1.84963 * height) - (4.6756 * age)
    else:
        bmr = 0  # Handle other cases as needed

    # Construct user_info dictionary
    user_info = {'$set':{
        '_id':_id,
        'UID': UID,
        'name': name,
        'age': age,
        'weight': weight,
        'height': height,
        'sex': gender,
        'food': food,
        'meal': meal,
        'no_servings': no_servings,
        'calories': calories,
        'activity_select': activity_select,
        'specific_motion_select': specific_motion_select,
        'met': met,
        'duration': duration,
        'daytimeselect': daytimeselect,
        'bmr': bmr  # Include calculated BMR
    }}
    # Insert user_info into MongoDB collection
    user_collection.update_one({'_id': _id}, user_info)

    # Redirect to the form route (or wherever you want)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)