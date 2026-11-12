from sqlalchemy import Integer, String, Column, Float, Date, ForeignKey, create_engine
from sqlalchemy.orm import Session, declarative_base
from datetime import date, datetime, timedelta, timezone
import jwt

DB_PATH = "warehouse.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()

USERNAME = "milky"
PASSWORD = "2357"
ACCESS_TOCKEN_EXPIRY = 15
REFRESH_TOKEN_EXPIRY = 7*24*60
SECRET_KEY = "secret1234"
ALGORITHM = "HS256"


STATUSES = ["pending", "dispatched"]
BATCH_STATUSES = ["planned", "dispatched"]

class Packages(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    package_name = Column(String)
    destination = Column(String)
    weight = Column(Float)
    arrival_date = Column(Date)
    status = Column(String, default="pending")
    dispatch_batch_id = Column(Integer, ForeignKey("dispatch_batches.id"))

class DispatchBatches(Base):
    __tablename__ = "dispatch_batches"
    id = Column(Integer, primary_key=True)
    destination = Column(String)
    vehicle = Column(String)
    dispatch_status = Column(String, default="pending")
    dispatch_date = Column(Date)

Base.metadata.create_all(engine)

def verify_login(username, password, token_type):
    if username == USERNAME and password == PASSWORD:
        access_token = create_token(username=username, token_type="access")
        refresh_token = create_token(username=username, token_type="refresh")
        return {"access_token":access_token, "refresh_token":refresh_token}
    return None


def create_token(username, token_type):
    time = ACCESS_TOCKEN_EXPIRY
    if token_type == "refresh":
        time = REFRESH_TOKEN_EXPIRY

    payload = {
        "username": username,
        "token_type":token_type,
        "exp":datetime.now(timezone.utc) + timedelta(minutes=time)
    }
    token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token, token_type):
    try:
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        return payload["username"]
    except:
        return False
    if payload["token_type"] == token_type:
        return payoad["username"]
    return False


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

# E1
def add_package(package_name, destination, weight, arrival_date, status):
    session = Session(engine)
    package = Packages(
        package_name=package_name,
        destination=destination,
        weight=weight,
        arrival_date=arrival_date,
        status=status
    )
    session.add(package)
    session.commit()
    session.close()
    return "registered"

# E2
def get_package(package_id):
    session = Session(engine)
    package = session.get(Packages, package_id)
    session.close()
    if package is None:
        return "not_found"
    return package


# E3
def update_package(package_id, name=None, destination=None, weight=None, arrival_date=None, status=None):
    session = Session(engine)
    package = session.get(Packages, package_id)
    if package is None:
        session.close()
        return "not_found"
    if name is not None:
        package.name = name
    if destination is not None:
        package.destination = destination
    if weight is not None:
        package.weight = weight
    if arrival_date is not None:
        package.arrival_date = arrival_date
    if status is not None:
        package.status = status
    session.commit()
    session.close()
    return "updated"


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
def get_all_packages(destination=None, status=None, arrival_date=None):
    session = Session(engine)
    packages = session.query(Packages)
    if destination is not None:
        packages = packages.filter(Packages.destination == destination)
    if status is not None:
        packages = packages.filter(Packages.status == status)
    if arrival_date is not None:
        packages = packages.filter(Packages.arrival_date == arrival_date)
    result = packages.order_by(Packages.id).all()
    session.close()
    return result


# E6
def get_all_batches(destination=None, vehicle=None, status=None):
    session = Session(engine)
    batches = session.query(Batches)
    if destination is not None:
        batches = batches.filter(Batches.destination == destination)
    if vehicle is not None:
        batches = batches.filter(Batches.vehicle == vehicle)
    if status is not None:
        batches = batches.filter(Batches.status == status)
    result = []
    for batch in batches.order_by(Batches.id).all():
        result.append(batch_to_dict(session, batch))
    session.close()
    return result


# E7
def get_warehouse_statistics():
    session = Session(engine)
    packages = session.query(Packages).all()
    pending = 0
    dispatched = 0
    destination_counts = {}
    for package in packages:
        if package.status == "dispatched":
            dispatched += 1
        else:
            pending += 1
        destination_counts[package.destination] = destination_counts.get(package.destination, 0) + 1
    session.close()
    return {"total_received": len(packages), "total_pending": pending,
            "total_dispatched": dispatched, "destination_counts": destination_counts}

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

# Update Dispatch Status
def dispatch_batch(batch_id):
    session = Session(engine)
    batch = session.get(Batches, batch_id)
    if batch is None:
        session.close()
        return "not_found"
    if batch.status == "dispatched":
        session.close()
        return "already_dispatched"
    batch.status = "dispatched"
    packages = session.query(Packages).filter(Packages.batch_id == batch_id).all()
    for package in packages:
        package.status = "dispatched"
    session.commit()
    session.close()
    return "dispatched"