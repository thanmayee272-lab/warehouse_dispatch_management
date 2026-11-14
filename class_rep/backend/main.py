from fastapi import FastAPI, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
import functions
from pydantic import BaseModel
from datetime import date

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"])


class User(BaseModel):
    username: str
    password: str
    user_type: str 


class LoginIn(BaseModel):
    roll_no: str 
    password: str 


class NominationCreate(BaseModel):
    name: str
    position: str
    manifesto: str


class VoteCreate(BaseModel):
    candidate_id: int


class PhaseUpdate(BaseModel):
    phase: str


functions.initialize_database()

@app.get("/")
def hello():
    return {"message": "Welcome to Class_rep Movie"}

@app.post("/register")
def register(user: User):
    if functions.register_user(user_name=user.username, password=user.password, user_type=user.user_type):
        return {"message": "User registered successfully"}
    raise HTTPException(status_code=400, detail="User already exists")        


@app.post("/login")
def login(username: str = Body(), password: str = Body()):
    token = functions.verify_login(username=username, password=password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid")
    return token


@app.post("/refresh")
def refresh(refresh_token = Header(None)):
    payload = functions.verify_token(token=refresh_token, token_type = "refresh")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or refresh token")
    access_token = functions.create_token(username=payload["username"], user_type=payload["user_type"], token_type = "access")
    return {"access_token": access_token}

# E1
@app.get("/candidates")
def get_candidates(position = None,approved_only = False, token = Header(None)):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    if position and position not in functions.POSITIONS:
        raise HTTPException(status_code=422,detail="Invalid position")
    return functions.get_all_candidates(position, approved_only)

# E2
@app.get("/candidates/{candidate_id}")
def candidate(candidate_id: int, token = Header(None)):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    result = functions.get_candidate(candidate_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Candidate not found")
    return result

# E3
@app.post("/candidates")
def nominate(nomination:NominationCreate, token = Header(None)):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    if nomination.position not in functions.POSITIONS:
        raise HTTPException(status_code=422, detail="Invalid position")
    if len(nomination.manifesto) < 30:
        raise HTTPException(status_code=422, detail="Manifesto must contain at least 30 characters")
    result = functions.add_candidate(nomination.roll_no, nomination.name, nomination.position, nomination.manifesto)
    if result == "duplicate_roll":
        raise HTTPException(status_code=400, detail="This roll number already has an active nomination")
    if result == "invalid_position":
        raise HTTPException(status_code=422, detail="Invalid position")
    return {"message": "Candidate nominated successfully"}

# E4
@app.patch("/candidates/{candidate_id}/approve")
def approve_candidate(candidate_id: int, token = Header(None)):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    response = functions.approve_candidate(candidate_id)
    if response == "phase_closed":
        raise HTTPException(status_code=400, detail="Nominations are closed")
    if response == "not_found":
        raise HTTPException(status_code=404, detail="Candidate not found")
    if response == "not_nominated":
        raise HTTPException(status_code=400, detail="Only nominated candidates can be approved")
    return {"message": "Candidate approved successfully"}

# E5
@app.patch("/candidates/{candidate_id}/withdraw")
def withdraw_candidate(candidate_id: int, token = Header(None)):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    response = functions.withdraw_candidate(candidate_id, payload["roll_no"])
    if response == "phase_closed":
        raise HTTPException(status_code=400, detail="Nominations are closed")
    if response == "not_found":
        raise HTTPException(status_code=404, detail="Candidate not found")
    if response == "roll_mismatch":
        raise HTTPException(status_code=403, detail="Roll number does not match the candidate")
    if response == "already_withdrawn":
        raise HTTPException(status_code=400, detail="Candidate is already withdrawn")
    return {"message": "Nomination withdrawn successfully"}

# E6
@app.get("/election/phase")
def get_election_phase(token = Header(None)):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    response = functions.get_election_phase()
    if response == "no_election":
        raise HTTPException(status_code=404, detail="Election not found")
    return {"phase": response}

# E7
@app.patch("/election/phase")
def change_phase(update:PhaseUpdate, token = Header(None)):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    result = functions.change_phase(update.phase)
    if result == "no_election":
        raise HTTPException(status_code=404, detail="Election not found")
    if result == "invalid_phase":
        raise HTTPException(status_code=400, detail="Invalid election phase")
    if result == "no_candidate":
        raise HTTPException(status_code=400, detail="Every position must have at least one approved candidate")
    return result

# E8
@app.post("/votes", status_code=201)
def vote(vote:VoteCreate, token = Header(None)):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    if vote.voter_roll == "":
        raise HTTPException(status_code=422,detail="Empty roll number")
    result = functions.cast_vote(vote.voter_roll, vote.candidate_id)
    if result == "voting_closed":
        raise HTTPException(status_code=400,detail="Voting is not open")
    if result == "not_found":
        raise HTTPException(status_code=404,detail="Candidate not found")
    if result == "not_approved":
        raise HTTPException(status_code=400,detail="Candidate not approved")
    if result == "already_voted":
        raise HTTPException(status_code=400,detail="Already voted for this position")

    return result

# E9
@app.get("/votes/{voter_roll}/positions")
def voted_positions(voter_roll: str, token = Header(None)):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    return functions.get_voted_positions(voter_roll)

# E10
@app.get("/results")
def get_final_results(token = Header(None)):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code = 401, detail = "Invalid or expiry token")
    result = functions.get_results()
    if result == "not_closed":
        raise HTTPException(status_code=403, detail="Election is not closed")
    return result