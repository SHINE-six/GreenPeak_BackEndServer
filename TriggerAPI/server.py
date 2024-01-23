from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

import uvicorn

app = FastAPI()

# ----------- Importing Firebase Admin SDK ----------------
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
# --------------------------------------------------------

# ----------- Defining Pydantic Models -------------------
class IotItem(BaseModel):
    name: str
    description: str = None
    onStatus: bool
    location: str
    abnormalStatus: bool = False
    currentData: dict = {
        "time": [datetime.now().time().strftime("%H:%M")],
        "date": [datetime.now().date().strftime("%d/%m/%Y")],
        "voltage": [None],
        "current": [None],
        "power": [None],
    }
    schedule: dict = {
        "day": [None],  # string
        "timeOn": [None], 
        "timeOff": [None],
    }


@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/items")
async def read_items():
    docs = db.collection('IoTDevices').stream()
    items = []
    for doc in docs:
        items.append(doc.to_dict())
    return {"items": items}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    doc_ref = db.collection('IoTDevices').document(str(item_id))
    doc = doc_ref.get()
    if doc.exists:
        return {"item": doc.to_dict()}
    else:
        return {"error": "Item not found"}
    
@app.post("/items")
async def create_item(item: IotItem):
    doc_ref = db.collection('IoTDevices').document()
    doc_ref.set({
        "name": item.name,
        "description": item.description,
        "onStatus": item.onStatus,
        "location": item.location,
        "abnormalStatus": item.abnormalStatus,
        "currentData": item.currentData,
        "schedule": item.schedule,
    })
    return {"success": "Item created"}

@app.put("/items/{item_id}/onStatus")
async def negate_onStatus(item_id: str):
    doc_ref = db.collection('IoTDevices').document(str(item_id))
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.update({
            "onStatus": not doc.to_dict()["onStatus"]
        })
        return {"success": "Item updated"}
    else:
        return {"error": "Item not found"}

@app.put("/items/{item_id}/abnormalStatus")
async def negate_abnormalStatus(item_id: str):
    doc_ref = db.collection('IoTDevices').document(str(item_id))
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.update({
            "abnormalStatus": not doc.to_dict()["abnormalStatus"]
        })
        return {"success": "Item updated"}
    else:
        return {"error": "Item not found"}

@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    doc_ref = db.collection('IoTDevices').document(str(item_id))
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.delete()
        return {"success": "Item deleted"}
    else:
        return {"error": "Item not found"}
    
@app.post("/items/{item_id}/currentData")
async def add_currentData(item_id: str, data: dict):
    doc_ref = db.collection('IoTDevices').document(str(item_id))
    doc = doc_ref.get()
    data["time"] = datetime.now().time().strftime("%H:%M")
    data["date"] = datetime.now().date().strftime("%d/%m/%Y")
    
    if doc.exists:
        currentData = doc.to_dict().get("currentData", {})

        for attr in ["voltage", "current", "power"]:
            if attr not in data:
                data[attr] = None
        
        updated_data = {
            "time": currentData.get("time", []) + [data["time"]],
            "date": currentData.get("date", []) + [data["date"]],
            "voltage": currentData.get("voltage", []) + [data["voltage"]],
            "current": currentData.get("current", []) + [data["current"]],
            "power": currentData.get("power", []) + [data["power"]],
        }
        
        doc_ref.update({"currentData": updated_data})
        return {"success": currentData}
    else:
        return {"error": "Item not found"}


@app.post("/items/{item_id}/schedule")
async def add_schedule(item_id: str, data: dict):
    doc_ref = db.collection('IoTDevices').document(str(item_id))
    doc = doc_ref.get()
    if doc.exists:
        schedule = doc.to_dict().get("schedule", {})
        
        if all(key in data for key in ["day", "timeOn", "timeOff"]):
            updated_data = {
                "day": schedule.get("day", []) + [data["day"]],
                "timeOn": schedule.get("timeOn", []) + [data["timeOn"]],
                "timeOff": schedule.get("timeOff", []) + [data["timeOff"]],
            }
            
            doc_ref.update({"schedule": updated_data})
            return {"success": updated_data}
        else:
            return {"error": "Missing required keys in data"}
    else:
        return {"error": "Item not found"}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 