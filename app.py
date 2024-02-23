# Flask Application
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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
ua = db['user_activity']
uf = db['user_food']

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

@app.route('/home')
def home1():
    return render_template('home.html', food_options=food_options, activity_options=activity_options, activities = activities)

@app.route('/login')
def log_page():
    return render_template('login.html')

@app.route('/register')
def reg():
    return render_template('register.html')

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
    #print("Activities:", activities)
    return render_template('form.html', food_options=food_options, activity_options=activity_options, activities=activities, user_info=user_info)
@app.route('/users', methods=['GET', 'POST'])
def users():
    try:
        # Fetch all users
        uid = request.args.get("uid")
        # print(uid)
        users_data = pd.DataFrame(list(user_collection.find({'UID': int(uid)})))
        res = users_data.to_dict(orient='records')
        food_data = pd.DataFrame(list(uf.find({'UID': str(uid)})))
        # fd = food_data.to_dict(orient='records')
        act_data = pd.DataFrame(list(ua.find({'UID': str(uid)})))
        if request.method == 'POST':
            date = request.form.get('date_input')
            act_data['daytimeselect'] = pd.to_datetime(act_data['daytimeselect'])
            act_data = act_data[act_data['daytimeselect'] == date]
            food_data['daytimeselect'] = pd.to_datetime(food_data['daytimeselect'])
            food_data = food_data[food_data['daytimeselect'] == date]
        ad = act_data.to_dict(orient='records')
        try:
            filtered_list_of_dicts = [{key: d[key] for key in ['METs', 'duration', 'daytimeselect']} for d in ad]
            act_list = pd.DataFrame(filtered_list_of_dicts)
            hrd = (act_list['duration']) / 60
            mval = act_list['METs']
            met_duration = mval * hrd
            sum_met_duration = met_duration.sum()
        except (KeyError, ValueError):
            sum_met_duration = 0

        try:
            filtered_list_of_dicts2 = [{key: d[key] for key in ['weight', 'height', 'bmr', 'age']} for d in res]
            info_list = pd.DataFrame(filtered_list_of_dicts2)
        except KeyError:
            info_list = pd.DataFrame()

        try:
            total_calories_out = sum_met_duration * info_list.get('weight', 0)
            food_data['total'] = food_data['calories'] * food_data['no_servings']
            sum_calories = food_data['total'].sum()
            NCD = sum_calories - info_list.get('bmr', 0) - total_calories_out
        except KeyError:
            total_calories_out = 0
            sum_calories = 0
            NCD = 0

        # Iterate over unique user IDs
        return render_template('users.html', user=res, fd=food_data.to_dict(orient='records'), sc=sum_calories, UID=uid, activities=ad, NCD=NCD, total_calories_out=total_calories_out)
    except Exception as e:
        # Log or handle the error appropriately
        print(f"An error occurred: {e}")
        # Return an error page or appropriate response
        return render_template('users.html',user=res)  # or 'error.html' depending on your design

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
    #print(user_datat)

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
        #print(user_data)
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
        #print(f"DEBUG: Total calories out: {total_calories_out}")

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

@app.route('/submit_login', methods=['POST'])
def submit_login():

    # Extract form data
    UID = int(request.form['UID'])
    name = request.form['name']
    print(UID,name)

    # Check if UID already exists
    existing_user = user_collection.find_one({'UID': UID})
    if existing_user:
        # If UID exists, verify that the name
        if existing_user['name'] != name:
            flash('Please Check The input.', 'error')
            return redirect(url_for('log_page'))
    # Redirect to the form route (or wherever you want)
    return redirect(url_for('users', uid=[UID]))

@app.route('/newsubmit', methods=['POST'])
def submit_form_new():
    # Get form data from request

    # Extract form data
    UID = int(request.form['UID'])
    name = request.form['name']
    age = int(request.form['age'])
    weight = float(request.form['weight'])
    height = float(request.form['height'])
    gender = request.form['sex']
    if gender == "male":
        bmr = 664.730 + (13.7516 * weight) + (5.0033 * height) - (6.7550 * age)
    elif gender == "female":
        bmr = 665.095 + (9.5634 * weight) + (1.84963 * height) - (4.6756 * age)
    else:
        bmr = 0  # Handle other cases as needed

    existing_user = user_collection.find_one({'UID': UID})
    if existing_user:
        return jsonify({'error': 'UID already exists. Please choose another UID.'})
    # Redirect to the form route (or wherever you want)

    user_info = {
        'UID': UID,
        'name': name,
        'age': age,
        'weight': weight,
        'height': height,
        'sex': gender,
        'bmr': bmr}
    user_collection.insert_one(user_info)
    time.sleep(5)
    return redirect(url_for('home'))

@app.route('/submit_food', methods=['POST'])
def edit_sub_form_food():
    # Extract form data
    client = MongoClient('mongodb://localhost:27017/')
    db = client['net_calorie_tracker']
    uf = db['user_food']
    _id = request.form['_id']
    print(_id)
    UID = request.form['UID']
    food = request.form['food']
    meal = request.form['meal']
    no_servings = int(request.form['no_servings'])
    calories = float(request.form['calories'])
    daytimeselect = request.form.get('date_input')

    # Construct user_info dictionary
    user_info = {'$set':{
        '_id':_id,
        'UID': UID,
        'food': food,
        'meal': meal,
        'no_servings': no_servings,
        'calories': calories,
        'daytimeselect': daytimeselect,
    }}
    # Insert user_info into MongoDB collection
    uf.update_one({'_id': _id}, user_info)

    # Redirect to the form route (or wherever you want)
    return redirect(url_for('users'))

@app.route('/submit_activities', methods=['POST'])
def edit_sub_form_activities():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['net_calorie_tracker']
    user_collection = db['users']
    # Extract form data
    motion_met_dict = dict(zip(activities_data['SPECIFIC MOTION'], activities_data['METs']))
    _id = ObjectId(user_collection.find_one({'_id': _id}))
    UID = int(user_collection.find_one({'UID': UID}))
    name = user_collection.find_one({'name': name})
    activity_select = request.form.get('activity_select')
    specific_motion_select = request.form.get('specific_motion_select')
    met = motion_met_dict.get(specific_motion_select)
    duration = float(request.form.get('duration'))
    daytimeselect = request.form.get('date_input')


    # Construct user_info dictionary
    user_info = {'$set':{
        '_id':_id,
        'UID': UID,
        'name': name,
        'activity_select': activity_select,
        'specific_motion_select': specific_motion_select,
        'met': met,
        'duration': duration,
        'daytimeselect': daytimeselect
    }}
    # Insert user_info into MongoDB collection
    ua.update_one({'_id': _id}, user_info)

    # Redirect to the form route (or wherever you want)
    return redirect(url_for('users'))

@app.route('/submit_food_new', methods=['POST'])
def newt_sub_form_food():
    # Extract form data
    client = MongoClient('mongodb://localhost:27017/')
    db = client['net_calorie_tracker']
    user_collection = db['users']
    UID = int(user_collection.find_one({'UID': UID}))
    name = user_collection.find_one({'name': name})
    sex = user_collection.find_one({'sex': sex})
    food = request.form['food']
    meal = request.form['meal']
    no_servings = int(request.form['no_servings'])
    calories = float(request.form['calories'])
    daytimeselect = request.form.get('date_input')

    # Construct user_info dictionary
    user_info = {
        '_id':_id,
        'UID': UID,
        'name': name,
        'sex': sex,
        'food': food,
        'meal': meal,
        'no_servings': no_servings,
        'calories': calories,
        'daytimeselect': daytimeselect,
    }
    # Insert user_info into MongoDB collection
    uf.insert_one(user_info)

    # Redirect to the form route (or wherever you want)
    return redirect(url_for('users'))

@app.route('/submit_activities_new', methods=['POST'])
def new_sub_form_activities():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['net_calorie_tracker']
    user_collection = db['users']
    # Extract form data
    motion_met_dict = dict(zip(activities_data['SPECIFIC MOTION'], activities_data['METs']))
    _id = ObjectId(user_collection.find_one({'_id': _id}))
    UID = int(user_collection.find_one({'UID': UID}))
    name = user_collection.find_one({'name': name})
    sex = user_collection.find_one({'sex': sex})
    activity_select = request.form.get('activity_select')
    specific_motion_select = request.form.get('specific_motion_select')
    met = motion_met_dict.get(specific_motion_select)
    duration = float(request.form.get('duration'))
    daytimeselect = request.form.get('date_input')


    # Construct user_info dictionary
    user_info = {
        '_id':_id,
        'UID': UID,
        'name': name,
        'sex' : sex,
        'activity_select': activity_select,
        'specific_motion_select': specific_motion_select,
        'met': met,
        'duration': duration,
        'daytimeselect': daytimeselect
    }
    # Insert user_info into MongoDB collection
    ua.insert_one(user_info)

    # Redirect to the form route (or wherever you want)
    return redirect(url_for('users'))

@app.route('/fusers')
def fusers():
    # Fetch all users
    uid = request.args.get("uid")
    print("abc",uid)
    food_data = pd.DataFrame(list(uf.find({'UID': int(uid)})))
    fd = food_data.to_dict(orient='records')
    _id = ObjectId(_id)
    user_datat = user_collection.find({'UID': int(uid)})
    if user_datat:
        # Extract UID from user_data
        UIDx = user_datat.get('UID')
        user_data_t = pd.DataFrame(list(uf.find({'UID': UIDx})))
        user_data = user_data_t.to_dict(orient='records')
        filtered_list_of_dicts = [{key: d[key] for key in ['food', 'calories', 'daytimeselect']} for d in user_data]
        food_list = pd.DataFrame(filtered_list_of_dicts)
        if request.method == 'POST':
            date = request.form.get('date_input')
            food_list['daytimeselect'] = pd.to_datetime(food_list['daytimeselect'])
            food_list = food_list[food_list['daytimeselect'] == date]
        food_list['calories'] = pd.to_numeric(food_list['calories'], errors='coerce')
        sum_cal = food_list['calories'].sum()
        hrd = (food_list['duration'])/60
        food_list['met_duration'] = food_list['met'] * hrd
        sum_met_duration = food_list['met_duration'].sum()
        sum_calories = food_list['calories'].sum()
        food_list = food_list.to_dict('records')

        total_calories_out = sum_met_duration * wt_avg
        NCD = sum_calories - bmr - total_calories_out
        #print(f"DEBUG: Total calories out: {total_calories_out}")

        return render_template('view_food.html', res=user_data, total_calories_out=total_calories_out, fd=fd)

    # Iterate over unique user IDs
    return render_template('view_food.html', fd=fd)

@app.route('/fact')
def fact():
    # Fetch all users
    uid = request.args.get("uid")
    print(uid)
    act_data = pd.DataFrame(list(ua.find({'UID': int(uid)})))
    ad = act_data.to_dict(orient='records')
    print(ad)
    # Iterate over unique user IDs
    return render_template('view_act.html', ad=ad)

@app.route('/edit_food/<_id>')
def edit_food(_id):
    _id = ObjectId(_id)
    print(_id)
    client = MongoClient('mongodb://localhost:27017/')
    db = client['net_calorie_tracker']
    food_data_t = db["food_data"]
    food_data1 = pd.DataFrame(list(food_data_t.find()))
    #print(food_data1)
    user_t = pd.DataFrame(list(uf.find_one({'_id': _id})))
    res = user_t.to_dict(orient='records')
    food_data = food_data1.to_dict(orient='records')
    return render_template('edit_food.html',res = res, food_data = food_data, _id=id)

@app.route('/add_food')
def add_food():
    uid = request.args.get("UID")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['net_calorie_tracker']
    food_data_t = db["food_data"]
    food_data1 = pd.DataFrame(list(food_data_t.find()))
    food_data = food_data1.to_dict(orient='records')
    return render_template('add_food.html', res= food_data, uid=uid)

@app.route('/add_food_submit/', methods=['POST'])
def add_food_submit():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['net_calorie_tracker']
    uf = db['user_food']
    UID = request.form['UID']
    food = request.form['food']
    meal = request.form['meal']
    no_servings = int(request.form['no_servings'])
    calories = float(request.form['calories'])
    daytimeselect = request.form.get('date_input')
    print(UID)

    # Construct user_info dictionary
    user_info = {
        'UID':UID,
        'food': food,
        'meal': meal,
        'no_servings': no_servings,
        'calories': calories,
        'daytimeselect': daytimeselect,
    }
    # Insert user_info into MongoDB collection
    uf.insert_one(user_info)

    # Redirect to the form route (or wherever you want)
    return redirect(url_for('users', uid=UID))

@app.route('/add_acti')
def add_acti():
    uid = request.args.get("UID")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['net_calorie_tracker']
    food_data_t = db['user_activity']
    food_data1 = pd.DataFrame(list(food_data_t.find()))
    food_data = food_data1.to_dict(orient='records')
    activity_dict = {}

    for index, row in activities_data.iterrows():
        activity = row['ACTIVITY']
        specific_motion = row['SPECIFIC MOTION']
        mets = row['METs']

        if activity not in activity_dict:
            activity_dict[activity] = {}

        activity_dict[activity][specific_motion] = mets

    print(activity_dict)
    return render_template('add_acti.html', res= food_data, activities =activities, uid=uid, met=met, activity_dict = activity_dict)

@app.route('/add_acti_submit/', methods=['POST'])
def add_acti_submit():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['net_calorie_tracker']
    ua = db['user_activity']
    UID = request.form['UID']
    activity_select = request.form['activity_select']
    specific_motion_select = request.form['specific_motion_select']
    duration = int(request.form['duration'])
    METs = float(request.form['METs'])
    daytimeselect = request.form.get('date_input')
    print(UID)

    # Construct user_info dictionary
    user_info = {
        'UID':UID,
        'activity_select': activity_select,
        'specific_motion_select': specific_motion_select,
        'METs': METs,
        'duration': duration,
        'daytimeselect': daytimeselect,
    }
    # Insert user_info into MongoDB collection
    ua.insert_one(user_info)

    # Redirect to the form route (or wherever you want)
    return redirect(url_for('users', uid=UID))


if __name__ == '__main__':
    app.run(debug=True)