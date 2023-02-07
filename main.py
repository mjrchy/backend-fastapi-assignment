from fastapi import FastAPI, HTTPException, Body
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel
import os
import urllib
from dotenv import load_dotenv

user = os.getenv('user')
password = urllib.parse.quote(os.getenv('password'))

DATABASE_NAME = "hotel"
COLLECTION_NAME = "reservation"
MONGO_DB_URL = "mongodb://{user}:{password}@mongo.exceed19.online"
MONGO_DB_PORT = 8443

class Reservation(BaseModel):
    name : str
    start_date: date
    end_date: date
    room_id: int

client = MongoClient(f"{MONGO_DB_URL}:{MONGO_DB_PORT}/?authMechanism=DEFAULT")

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()

def room_avaliable(room_id: int, start_date: str, end_date: str):
    query={"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0

@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name:str):
    return {"result": list(collection.find({"name": name}))}

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    return {"result": list(collection.find({"room_id": room_id}))}

@app.post("/reservation",status_code=201)
def reserve(reservation : Reservation):
    collection.update_one({"name": reservation.name, "start_date": reservation.start_date, "end_date": reservation.end_date, "room_id": reservation.room_id})
    return {"msg": "already reserve"}

@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    collection.update_one({"name": reservation.name, "start_date": reservation.start_date, "end_date": reservation.end_date, "room_id": reservation.room_id}, {"$set": {"start_date": new_start_date, "end_date": new_end_date}})
    return {"msg": "already update"}

@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    collection.delete_one({"name": reservation.name, "start_date": reservation.start_date, "end_date": reservation.end_date, "room_id": reservation.room_id}) 
    return {"msg": "already delete"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
