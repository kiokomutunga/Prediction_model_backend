
from pymongo import MongoClient

import os


Mongo_URl = "mongodb://localhost:27017"
client = MongoClient(Mongo_URl)

database = client["tomato_disease"]

disease_collection = database["diseases"]

prediction_collection = database["prediction"]

def get_disease_info(disease_name):
    return disease_collection.find_one(
        {"key": disease_name},
        {"_id": 0}
    )

def get_all_diseases():
    return list(
        disease_collection.find({}, {"_id": 0})
    )