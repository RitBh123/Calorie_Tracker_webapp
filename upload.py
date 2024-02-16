import pandas as pd
from pymongo import MongoClient

# MongoDB configuration
client = MongoClient('localhost', 27017)
db = client['net_calorie_tracker']
collection1 = db['activities_data']
collection2 = db['food_data']

def upload_excel_to_mongodb1(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)
    # Convert dataframe to dictionary
    data = df.to_dict(orient='records')
    # Insert data into MongoDB
    collection1.insert_many(data)
    print('File uploaded successfully and data stored into MongoDB.')
def upload_excel_to_mongodb2(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)
    # Convert dataframe to dictionary
    data = df.to_dict(orient='records')
    # Insert data into MongoDB
    collection2.insert_many(data)
    print('File uploaded successfully and data stored into MongoDB.')

if __name__ == '__main__':
    # Path to the Excel file
    excel_file_path1 = 'db/activities_data.xlsx'
    excel_file_path2 = 'db/food_data.xlsx'
    upload_excel_to_mongodb1(excel_file_path1)
    upload_excel_to_mongodb2(excel_file_path2)