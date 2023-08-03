from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from models import User, Profile
from database import SessionLocal
import os

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_profile_picture(profile_picture, user_id):
    upload_dir = "uploads/profile_pictures/"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}profile_{user_id}.jpg"
    with open(file_path, "wb") as f:
        f.write(profile_picture.file.read())
    return file_path


@router.post("/register/", tags=["Register New User."])
def register_user(
    full_name: str,
    email: str,
    password: str,
    phone: str,
    profile_picture: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user_by_email = db.query(User).filter(User.email == email).first()
    user_by_phone = db.query(User).filter(User.phone == phone).first()

    if user_by_email or user_by_phone:
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    user = User(full_name=full_name, email=email, password=password, phone=phone)
    db.add(user)
    db.flush()

    profile_picture_path = save_profile_picture(profile_picture, user.id)
    profile = Profile(profile_picture=profile_picture_path, user_id=user.id)
    db.add(profile)
    db.commit()
    return {"message": "User registered successfully"}


@router.get("/user/{user_id}/")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "profile_picture": user.profile.profile_picture if user.profile else None,
    }


@router.get("/users/", tags=["Get Single User."])
def get_all_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    users_data = []
    for user in users:
        profile_picture = user.profile.profile_picture if user.profile else None
        users_data.append({
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "profile_picture": profile_picture,
        })
    return users_data


@router.put("/user/{user_id}/update/", tags=["Update the User Details."])
def update_user_details(
    user_id: int,
    full_name: str,
    email: str,
    password: str,
    phone: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.full_name = full_name
    user.email = email
    user.password = password
    user.phone = phone
    db.commit()
    return {"message": "User details updated successfully"}


@router.put("/user/{user_id}/update-profile-photo/", tags=["Update the Profile Photo."])
def update_profile_photo(
    user_id: int,
    profile_picture: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.profile and user.profile.profile_picture:
        try:
            os.remove(user.profile.profile_picture)
        except OSError:
            pass
    profile_picture_path = save_profile_picture(profile_picture, user.id)

    if not user.profile:
        user.profile = Profile()
    user.profile.profile_picture = profile_picture_path
    db.commit()
    return {"message": "Profile picture updated successfully"}


@router.delete("/user/{user_id}/", tags=["Delete User."])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.profile and user.profile.profile_picture:
        try:
            os.remove(user.profile.profile_picture)
        except OSError:
            pass
    db.delete(user.profile)
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
