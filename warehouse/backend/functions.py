from sqlalchemy import Integer, String, Column, Float, Date, ForeignKey, create_engine
from sqlalchemy.orm import Session, declarative_base
from datetime import date

DB_PATH = "warehouse.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()

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
    if "arrival_date" in data:
        data["arrival_date"] = date.fromisoformat(data["arrival_date"])
    for key, value in data.items():
        setattr(package, key, value)
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
def get_all_packages(destination=None, status=None, arrival_date=None):
    session = Session(engine)
    packages = session.query(Packages)
    if destination:
        packages = packages.filter(Packages.destination == destination)
    if status:
        packages = packages.filter(Packages.status == status)
    if arrival_date:
        arrival_date = date.fromisoformat(arrival_date)
        packages = packages.filter(Packages.arrival_date == arrival_date)
    response = [package_details(p) for p in packages.all()]
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

# Update Dispatch Status
def update_dispatch_status(batch_id, dispatch_status):
    session = Session(engine)

    batch = session.get(DispatchBatches, batch_id)

    if batch is None:
        session.close()
        return "not_found"

    batch.dispatch_status = dispatch_status

    if dispatch_status == "dispatched":
        batch.dispatch_date = date.today()

    packages = session.query(Packages).filter(
        Packages.dispatch_batch_id == batch_id
    ).all()

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