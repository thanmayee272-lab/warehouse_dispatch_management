from sqlalchemy import Integer, String, Column, Float, Date, ForeignKey, create_engine
from sqlalchemy.orm import Session, declarative_base
from datetime import datetime, timedelta, timezone, date
import jwt 
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


ph = PasswordHasher()

DB_PATH = "warehouse.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()


USERNAME = "milky"
PASSWORD = "2357"

ACCESS_TOKEN_EXPIRY = 15
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60
SECRET_KEY = "secret1234"
ALGORITHM = "HS256"


class Packages(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    package_name = Column(String)
    destination = Column(String)
    weight = Column(Float)
    arrival_date = Column(Date)
    status = Column(String, default="pending")
    dispatch_batch_id = Column(Integer, ForeignKey("dispatch_batches.id"), nullable=True)

class DispatchBatches(Base):
    __tablename__ = "dispatch_batches"
    id = Column(Integer, primary_key=True)
    destination = Column(String)
    vehicle = Column(String)
    dispatch_status = Column(String, default="pending")
    dispatch_date = Column(Date, nullable=True)


class User(Base):
    __tablename__ = "user"
    user_id = Column[int](Integer, primary_key=True)
    username = Column[str](String)
    password = Column[str](String)
    user_type = Column[str](String)


Base.metadata.create_all(engine)


def package_details(package):
    return {
        "id": package.id,
        "package_name": package.package_name,
        "destination": package.destination,
        "weight": package.weight,
        "arrival_date": str(package.arrival_date),
        "status": package.status,
        "dispatch_batch_id": package.dispatch_batch_id
    }

# -----------user------------
def register_user(user_name:str, password:str, user_type:str):
    if user_type not in ["manager", "dispatcher"]:
        raise HTTPException(status_code=422, detail="Invalid user type")
    session = Session(engine)
    user_exists = session.query(User).filter_by(username=user_name).first()
    if user_exists:
        session.close()
        return False
    session.add(User(username=user_name, password=ph.hash(password), user_type=user_type))
    session.commit()
    session.close()
    return True


def verify_login(username, password):
    session = Session(engine)
    user = session.query(User).filter_by(username=username).first()
    if user is None:
        session.close()
        return False
    try:
        ph.verify(user.password, password)
    except VerifyMismatchError:
        session.close()
        return False

    access_token = create_token(username=username,user_type=user.user_type, token_type="access")
    refresh_token = create_token(username=username,user_type=user.user_type, token_type="refresh")
    session.close()
    return {"access_token": access_token, "refresh_token": refresh_token}


def create_token(username,user_type, token_type):
    time = ACCESS_TOKEN_EXPIRY
    if token_type == "refresh":
      time = REFRESH_TOKEN_EXPIRY
    payload = {
        "username": username,
        "token_type": token_type,
        "user_type": user_type,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=time),
        }
    token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)
    return token 


def verify_token(token, token_type):
    try:
     payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except:
        return False
    if payload["token_type"] == token_type:
        return payload
    return False


# E1
def add_package(package_name, destination, weight, arrival_date):
    session = Session(engine)
    package = Packages(
        package_name=package_name,
        destination=destination,
        weight=weight,
        arrival_date=date.fromisoformat(arrival_date),
        status="pending"
    )
    session.add(package)
    session.commit()
    session.refresh(package)
    response = package_details(package)
    session.close()
    return response

# E2
def get_package(package_id):
    session = Session(engine)
    package = session.get(Packages, package_id)
    if package is None:
        session.close()
        return None
    response = package_details(package)
    session.close()
    return response

# E3
def update_package(package_id, data):
    session = Session(engine)
    package = session.get(Packages, package_id)
    if package is None:
        session.close()
        return "not_found"
    if package.status == "dispatched":
        session.close()
        return "already_dispatched"
    if package.dispatch_batch_id is not None:
        session.close()
        return "already_assigned"
    if "package_name" in data:
        package.package_name = data["package_name"]
    if "destination" in data:
        package.destination = data["destination"]
    if "weight" in data:
        package.weight = data["weight"]
    if "arrival_date" in data:
        package.arrival_date = data["arrival_date"]
    session.commit()
    response = package_details(package)
    session.close()
    return response

# E4
def delete_package(package_id):
    session = Session(engine)
    package = session.get(Packages, package_id)
    if package is None:
        session.close()
        return "not_found"
    if package.status == "dispatched":
        session.close()
        return "already_dispatched"
    session.delete(package)
    session.commit()
    session.close()
    return "deleted"

# E5
def get_all_packages():
    session = Session(engine)
    packages = session.query(Packages).all()
    response = [package_details(p) for p in packages]
    session.close()
    return response

# E6
def get_all_dispatch_batches(destination=None, vehicle=None, dispatch_status=None):
    session = Session(engine)
    batches = session.query(DispatchBatches)
    if destination:
        batches = batches.filter(DispatchBatches.destination == destination)
    if vehicle:
        batches = batches.filter(DispatchBatches.vehicle == vehicle)
    if dispatch_status:
        batches = batches.filter(DispatchBatches.dispatch_status == dispatch_status)
    response = []
    for batch in batches.all():
        packages = session.query(Packages).filter(
            Packages.dispatch_batch_id == batch.id).all()
        response.append({
            "id": batch.id,
            "destination": batch.destination,
            "vehicle": batch.vehicle,
            "dispatch_status": batch.dispatch_status,
            "dispatch_date": str(batch.dispatch_date) if batch.dispatch_date else None,
            "package_ids": [p.id for p in packages]
        })
    session.close()
    return response

# E7
def get_warehouse_statistics():
    session = Session(engine)
    total = session.query(Packages).count()
    dispatched = session.query(Packages).filter(
        Packages.status == "dispatched"
    ).count()
    packages = session.query(Packages).all()
    destinations = {}
    for package in packages:
        name = package.destination
        if name not in destinations:
            destinations[name] = 0
        destinations[name] += 1
    response = {
        "total_packages": total,
        "pending_packages": total - dispatched,
        "dispatched_packages": dispatched,
        "destination_wise_count": destinations
    }
    session.close()
    return response

# E8
def create_dispatch_batch(destination, vehicle, package_ids, dispatch_status):
    session = Session(engine)
    if len(package_ids) == 0:
        session.close()
        return "no_packages"
    packages = []
    for package_id in package_ids:
        package = session.get(Packages, package_id)
        if package is None:
            session.close()
            return "package_not_found"
        if package.status == "dispatched":
            session.close()
            return "already_dispatched"
        if package.dispatch_batch_id is not None:
            session.close()
            return "already_assigned"
        if package.destination != destination:
            session.close()
            return "destination_mismatch"
        packages.append(package)
    batch = DispatchBatches(
        destination=destination,
        vehicle=vehicle,
        dispatch_status=dispatch_status)
    if dispatch_status == "dispatched":
        batch.dispatch_date = date.today()
    session.add(batch)
    session.commit()
    session.refresh(batch)
    for package in packages:
        package.dispatch_batch_id = batch.id
        package.status = "dispatched" if dispatch_status == "dispatched" else "assigned"
    session.commit()
    response = {
        "id": batch.id,
        "destination": batch.destination,
        "vehicle": batch.vehicle,
        "dispatch_status": batch.dispatch_status,
        "dispatch_date": str(batch.dispatch_date) if batch.dispatch_date else None,
        "package_ids": package_ids
    }
    session.close()
    return response


def update_dispatch_status(batch_id, dispatch_status):
    session = Session(engine)
    batch = session.get(DispatchBatches, batch_id)
    if batch is None:
        session.close()
        return "not_found"
    batch.dispatch_status = dispatch_status
    if dispatch_status == "dispatched":
        batch.dispatch_date = date.today()
    packages = session.query(Packages).filter(Packages.dispatch_batch_id == batch_id).all()
    for package in packages:
        package.status = dispatch_status

    session.commit()

    response = {
        "id": batch.id,
        "destination": batch.destination,
        "vehicle": batch.vehicle,
        "dispatch_status": batch.dispatch_status,
        "dispatch_date": str(batch.dispatch_date)
    }

    session.close()
    return response