from fastapi import FastAPI, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
import functions
from pydantic import BaseModel
from datetime import date

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)



class User(BaseModel):
    username: str
    password: str


class Package(BaseModel):
    package_name: str
    destination: str
    weight: float
    arrival_date: date


class PackageUpdate(BaseModel):
    package_name: str | None = None
    destination: str | None = None
    weight: float | None = None
    arrival_date: date | None = None


class DispatchBatches(BaseModel):
    destination: str
    vehicle: str
    package_ids: list[int]
    dispatch_status: str = "pending"


class DispatchBatchUpdate(BaseModel):
    dispatch_status: str
  

@app.get("/")
def hello():
    return {"message": "Welcome to Warehouse Dispatch Management System"}


@app.post("/register")
def register(user: User):
    if functions.register_user(user_name=user.username, password=user.password):
        return {"message": "User registered successfully"}
    raise HTTPException(status_code=400, detail="User already exists")        


@app.post("/login")
def login(user: User):
    token = functions.verify_login(username=user.username, password=user.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid")
    return token


@app.post("/refresh")
def refresh(refresh_token = Header(None)):
    username = functions.verify_token(token=refresh_token, token_type = "refresh")
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or refresh token")
    access_token = functions.create_token(username=user["username"], role=user["role"], token_type = "access")
    return {"access_token": access_token}


# E1
@app.post("/packages")
def register_package(package:Package, token = Header(None)):
    
    username = functions.verify_token(token=token, token_type = "access")
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    if package.weight <= 0:
        raise HTTPException(status_code=422, detail="Incorrect weight")
    return functions.add_package(package.package_name, package.destination, package.weight, package.arrival_date)

# E2 
@app.get("/packages/{package_id}")
def get_package(package_id: int, token = Header(None)):
    username = functions.verify_token(token=token, token_type="access")
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    response = functions.get_package(package_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return response


# E3 
@app.patch("/packages/{package_id}")
def update_package(package_id: int, package: PackageUpdate, token = Header(None)):
    username = functions.verify_token(token=token, token_type = "access")
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    if package.weight is not None and package.weight <= 0:
        raise HTTPException(status_code=422, detail="Incorrect weight")
    data = {}
    if package.package_name is not None:
        data["package_name"] = package.package_name
    if package.destination is not None:
        data["destination"] = package.destination
    if package.weight is not None:
        data["weight"] = package.weight
    if package.arrival_date is not None:
        data["arrival_date"] = package.arrival_date
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="No update details provided")
    response = functions.update_package(package_id, data)
    if response == "not_found":
        raise HTTPException(status_code=404, detail="Package not found")
    if response == "already_dispatched":
        raise HTTPException(status_code=400, detail="Dispatched package cannot be updated")
    if response == "already_assigned":
        raise HTTPException(status_code=400, detail="Assigned package cannot be updated")
    return response

# E4 
@app.delete("/packages/{package_id}")
def delete_package(package_id: int, token = Header(None)):
    username = functions.verify_token(token=token, token_type = "access")
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    response = functions.delete_package(package_id)
    if response == "not_found":
        raise HTTPException(status_code=404, detail="Package not found")
    if response == "already_dispatched":
        raise HTTPException(status_code=400, detail="Dispatched package cannot be deleted")
    return {"message": "Package deleted successfully"}

# E5 
@app.get("/packages")
def get_packages(package_id: int = None, token = Header(None)):
    username = functions.verify_token(token=token, token_type = "access")
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    return functions.get_all_packages()

# E6
@app.get("/dispatch-batches")
def get_dispatch_batches(dispatch_status: str = None,token=Header(None)):
    username = functions.verify_token(token=token,token_type="access")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if dispatch_status is not None and dispatch_status not in ["pending", "dispatched"]:
        raise HTTPException(status_code=422, detail="Invalid dispatch status")
    return functions.get_all_dispatch_batches(None,dispatch_status,None)


# E7 
@app.get("/warehouse/statistics")
def warehouse_statistics(token = Header(None)):
    username = functions.verify_token(token=token, token_type = "access")
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    return functions.get_warehouse_statistics()

# E8
@app.post("/dispatch-batches")
def create_dispatch_batch(dispatch_batch: DispatchBatches,token=Header(None)):
    username = functions.verify_token(token=token,token_type="access")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if dispatch_batch.dispatch_status not in ["pending", "dispatched"]:
        raise HTTPException(status_code=422, detail="Invalid dispatch status")
    if len(dispatch_batch.package_ids) == 0:
        raise HTTPException(status_code=400, detail="No packages provided")
    response = functions.create_dispatch_batch(
        dispatch_batch.destination,
        dispatch_batch.vehicle,
        dispatch_batch.package_ids,
        dispatch_batch.dispatch_status
    )

    if response == "package_not_found":
        raise HTTPException(status_code=404, detail="Package not found")
    if response == "already_dispatched":
        raise HTTPException(status_code=400, detail="Package already dispatched")
    if response == "already_assigned":
        raise HTTPException(status_code=400, detail="Package already assigned")
    if response == "destination_mismatch":
        raise HTTPException(status_code=400, detail="Destination does not match")
    if response == "no_packages":
        raise HTTPException(status_code=400, detail="No packages provided")
    return response

# E9
@app.patch("/dispatch-batches/{batch_id}")
def update_dispatch_status(batch_id: int,dispatch_batch: DispatchBatchUpdate,token=Header(None)):
    username = functions.verify_token(token=token,token_type="access")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if dispatch_batch.dispatch_status not in ["pending", "dispatched"]:
        raise HTTPException(status_code=422, detail="Invalid dispatch status")
    response = functions.update_dispatch_status(batch_id,dispatch_batch.dispatch_status)
    if response == "not_found":
        raise HTTPException(status_code=404, detail="Dispatch batch not found")
    return response
