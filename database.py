
from pymongo import MongoClient, ASCENDING, DESCENDING

import os


Mongo_URl = "mongodb://localhost:27017"
client = MongoClient(Mongo_URl)

database = client["tomato_disease"]

disease_collection = database["diseases"]

prediction_collection = database["prediction"]

chat_collection = database["chat_sessions"]

#INDEXING FOR FASTER QUERIES
prediction_collection.create_index([("timestamp", DESCENDING)])
prediction_collection.create_index([("prediction", ASCENDING)])
chat_collection.create_index([("session_id", ASCENDING)], unique=True)
chat_collection.create_index([("scan_id",    ASCENDING)])
chat_collection.create_index([("updated_at", DESCENDING)])

def get_disease_info(disease_name):
    return disease_collection.find_one(
        {"key": disease_name},
        {"_id": 0}
    )

def get_all_diseases():
    return list(
        disease_collection.find({}, {"_id": 0})
    )

def get_chat_by_session(session_id: str) -> dict | None:
    
    session = chat_collection.find_one({"session_id": session_id})
    if session:
        session["_id"] = str(session["_id"])
    return session

def get_chat_by_scan(scan_id: str) -> dict | None:
    
    session = chat_collection.find_one({"scan_id": scan_id})
    if session:
        session["_id"] = str(session["_id"])
    return session

def get_disease_for_scan(prediction_key: str) -> dict | None:
    
    return get_disease_info(prediction_key)