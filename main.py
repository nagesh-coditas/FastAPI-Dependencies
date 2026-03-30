from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# ------------------ DB SETUP ------------------
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

Base.metadata.create_all(bind=engine)


app = FastAPI()

# ------------------ DEPENDENCIES ------------------
#1. Funcation Based Dependency

#1.1 DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#1.2 Auth Dependency
def get_current_user(token: str):
    if token != "secret-token":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"username": "Nagesh"}

# ------------------ ROUTES ------------------

# Create User (requires DB only)
@app.post("/users")
def create_user(name: str, db: Session = Depends(get_db)):
    user = User(name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

from fastapi import Depends
# Get Users (requires DB)
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# Protected route example
@app.get("/profile")
def profile(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return {"msg": f"Welcome {user['username']}", "all_users": db.query(User).all()}



# -----------------------------------------------------------------------------------------------------------------

#2.Class Based Dependency

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, token: str = Header(...)):
        # 🔐 Simulate token decoding (replace with JWT in real app)
        if token == "admin-token":
            user = {"name": "Nagesh", "role": "admin"}
        elif token == "user-token":
            user = {"name": "Nagesh", "role": "user"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 🔒 Authorization check
        if user["role"] not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")

        return user

# Only ADMIN can access
@app.get("/admin")
def admin_route(user=Depends(RoleChecker(["admin"]))):
    return {"msg": f"Welcome Admin {user['name']}"}


# ADMIN + MANAGER can access
@app.get("/manager")
def manager_route(user=Depends(RoleChecker(["admin", "manager"]))):
    return {"msg": f"Welcome Manager {user['name']}"}


# Any USER role can access
@app.get("/user")
def user_route(user=Depends(RoleChecker(["admin", "manager", "user"]))):
    return {"msg": f"Welcome User {user['name']}"}



# -----------------------------------------------------------------------------------------------------------------

#3.Nested Dependency
from fastapi import Header

def get_user_id(token: str = Header(..., description="Auth Token")) -> str:
    """Extract and validate user ID from token"""
    if token != "ABC":
        raise HTTPException(status_code=401, detail="Invalid token")
    return "user_123"  # Extract actual user ID from token

def get_current_user(user_id: str = Depends(get_user_id)) -> dict:
    """Fetch complete user details using user_id from db"""
    return {"user_id": user_id, "user": "Nagesh", "role": "admin"}

@app.get("/nested")
def nested(user=Depends(get_current_user)):
    return user