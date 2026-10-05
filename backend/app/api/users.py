from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.external_id == payload.external_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this external_id already exists")

    user = User(
        external_id=payload.external_id,
        username=payload.username or payload.external_id,
        role=UserRole.user,
        daily_limit=100,
        is_unlimited=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/by-external/{external_id}", response_model=UserOut)
def get_user_by_external(external_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.external_id == external_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.username is not None:
        user.username = payload.username
    if payload.daily_limit is not None:
        user.daily_limit = payload.daily_limit
    if payload.is_unlimited is not None:
        user.is_unlimited = payload.is_unlimited

    db.commit()
    db.refresh(user)
    return user
