from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, Token, LoginRequest, UpdateRoleRequest
from app.auth.jwt import hash_password, verify_password, create_access_token
from app.auth.deps import get_current_user, get_admin_user, get_superadmin_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.delete("/me", status_code=204)
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """自分自身のアカウントを削除する。"""
    db.delete(current_user)
    db.commit()


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@router.get("/users", response_model=list[UserResponse])
def list_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """全ユーザー一覧を返す（admin のみ）。"""
    return db.query(User).all()


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """指定したユーザーを削除する（admin のみ）。superadmin は削除不可。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_superadmin:
        raise HTTPException(status_code=403, detail="Cannot delete superadmin")
    db.delete(user)
    db.commit()


# ---------------------------------------------------------------------------
# Superadmin endpoints
# ---------------------------------------------------------------------------

@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    body: UpdateRoleRequest,
    superadmin: User = Depends(get_superadmin_user),
    db: Session = Depends(get_db),
):
    """ユーザーのロールを変更する（superadmin のみ）。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == superadmin.id and body.role != "superadmin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
    user.role = body.role
    db.commit()
    db.refresh(user)
    return user
