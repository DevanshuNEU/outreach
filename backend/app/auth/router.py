import uuid
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.auth.deps import hash_password, verify_password, create_token, get_current_user
from app.models.schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    db = get_db()
    existing = db.table("users").select("id").eq("username", req.username).execute()
    if existing.data:
        raise HTTPException(400, "Username already taken")

    user_id = str(uuid.uuid4())
    db.table("users").insert({
        "id": user_id,
        "username": req.username,
        "password_hash": hash_password(req.password),
    }).execute()

    # Create empty profile
    db.table("profiles").insert({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "full_name": req.username,
        "sign_off_block": "Best,\n" + req.username,
        "links_block": "",
        "projects": [],
    }).execute()

    token = create_token(user_id, req.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    db = get_db()
    result = db.table("users").select("*").eq("username", req.username).execute()
    if not result.data:
        raise HTTPException(401, "Invalid credentials")

    user = result.data[0]
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    token = create_token(user["id"], user["username"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    return UserOut(id=current_user["id"], username=current_user["username"])
