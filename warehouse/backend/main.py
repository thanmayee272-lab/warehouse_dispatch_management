from fastapi import FastAPI, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
import functions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/login")
def login(username:str, password:str):
    token = functions.verify_login(username=username, password=password, token_type=refresh)
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid")
    return token


@app.post("/refresh")
def refresh(refresh_token = Header(None)):
    username = functions.verify_token(token=refresh_token, token_type="refresh")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or Expired refresh token")
    access_token = functions.create_token(username=username, token_type="access")
    return {"access_token":access_token}


@app.get("/")
def hello():
    return {"message": "Welcome to Warehouse Dispatch Management System"}


@app.post("/packages")
def register_packages(package_name,destination,weight,arrival_date,status, token = Header(None)):
    username = functions.verify_token(token=token, token_type=token_type)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expairy token")
    if weight <= 0:
        raise HTTPException(status_code=422, detail="Incorrect weight")
    return functions.register_package(package_name=package_name,destination=destination,weight=weight,arrival_date=arrival_date,status=status)


@app.get("/packages")
def search_packages(destination=None, status=None, arrival_date=None, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expairy token")
    response = functions.get_package(package_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return response


@app.get("/packages/{package_id}")
def get_details(package_id, token = Header(None)):
    username = functions.verify_token(token=token,token_type="access")
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expairy token")
    package = functions.get_package(package_id=package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Not found")
    return package


@app.patch("/packages/{package_id}")
def update_package(package_id, destination=None, status=None, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expairy token")
    if functions.get_details(package_id=package_id) is None:
        raise HTTPException(status_code=404, detail="Not found")
    return functions.update_package(package_id=package_id, destination=destination, status=status)


@app.delete("/packages/{package_id}")
def delete_package(package_id, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expairy token")
    package = functions.get_details(package_id=package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Not found")
    if package["status"] == "dispatched":
        raise HTTPException(status_code=400, detail="already dispatched")
    functions.delete_package(package_id=package_id)
    return {"message": "Deleted"}


@app.get("/dispatch-batches")
def view_batches(destination, vehicle, dispatch_status, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expairy token")
    if dispatch_status and dispatch_status not in ["pending", "dispatched"]:
        raise HTTPException(status_code=422, detail="Invalid dispatch status")
    return functions.get_batches(destination=destination, vehicle=vehicle, dispatch_status=dispatch_status)


@app.get("/stats")
def get_stats(token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expairy token")
    return functions.get_stats()


@app.post("/dispatch-batches")
def add_data(vehicle, package_id, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expairy token")
    if functions.get_details(package_id=package_id) is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return functions.add_data(vehicle=vehicle, package_id=package_id)