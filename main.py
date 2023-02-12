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
    if type(name) !=  str:
        raise HTTPException(400, "Name should be string")
    reservation_list = []
    for item in collection.find({"name": name}, {"_id": False}):
        reservation_list.append(item)
    return {"result": reservation_list}

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    if room_id not in range(1,11):
        raise HTTPException(400, "room id should in range 1 to 10")
    reservation_list = []
    for item in collection.find({"room_id": room_id}, {"_id": False}):
        reservation_list.append(item)
    return {"result": reservation_list}

@app.post("/reservation")
def reserve(reservation : Reservation):
    if reservation not in range(1,11):
        raise HTTPException(400, "room id should in range 1 to 10")
    if not room_avaliable(reservation.room_id, str(reservation.start_date), str(reservation.end_date)):
        raise HTTPException(400, "room is unavailable")
    if not reservation.start_date <= reservation.end_date:
        raise HTTPException(400, "start date should be before end date")
    collection.update_one({"name": reservation.name, "start_date": reservation.start_date.strftime("%Y-%m-%d"), "end_date": reservation.end_date.strftime("%Y-%m-%d"), "room_id": reservation.room_id})
    return {"msg": "already reserve"}

@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    if not room_avaliable(reservation.room_id, str(reservation.start_date), str(reservation.end_date)):
        raise HTTPException(400, "room is unavailable")
    if not reservation.start_date <= reservation.end_date:
        raise HTTPException(400, "start date should be before end date")
    collection.update_one({"name": reservation.name, "start_date": reservation.start_date.strftime("%Y-%m-%d"), "end_date": reservation.end_date.strftime("%Y-%m-%d"), "room_id": reservation.room_id}, {"$set": {"start_date": new_start_date.isoformat(), "end_date": new_end_date.isoformat()}})
    return {"msg": "already update"}

@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    if collection.find_one({"id": reservation.room_id}):
        raise HTTPException(500, "Room id is not found")
    collection.delete_one({"name": reservation.name, "start_date": reservation.start_date.strftime("%Y-%m-%d"), "end_date": reservation.end_date.strftime("%Y-%m-%d"), "room_id": reservation.room_id}) 
    return {"msg": "already delete"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
