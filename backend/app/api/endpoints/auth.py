from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.models import User, AuditLog
from app.schemas.schemas import UserSignup, UserSignin, UserResponse, TokenResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["User Authentication (Task 3)"])

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserSignup, db: Session = Depends(get_db)):
    """Registers a new user, hashes password, and returns a signed JWT access token."""
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An account with email '{user_in.email}' already exists."
        )

    user = User(
        name=user_in.name,
        email=user_in.email.lower(),
        hashed_password=hash_password(user_in.password),
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Issue JWT token
    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})

    # Audit log
    audit = AuditLog(
        entity_type="user",
        entity_id=user.id,
        action="user_signup",
        old_value=None,
        new_value={"name": user.name, "email": user.email},
        performed_by="user"
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/signin", response_model=TokenResponse)
def signin(credentials: UserSignin, db: Session = Depends(get_db)):
    """Authenticates credentials and returns a signed JWT access token."""
    user = db.query(User).filter(User.email == credentials.email.lower()).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Protected endpoint: Returns the profile of the currently authenticated user."""
    return current_user
