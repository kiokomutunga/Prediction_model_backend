#install dependancies
from pymongo import MongoClient

import os

#include mongo url
Mongo_URl = "mongodb://localhost:27017"
client = MongoClient(Mongo_URl)
#call the mongo client from the mongo db
database = client["tomato_disease"]

disease_collection = database["diseases"]
 #the database collection
def get_disease_info(disease_name):
    return disease_collection.find_one(
        {"name": disease_name},
        {"_id": 0}
    )