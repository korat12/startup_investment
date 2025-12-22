# utils/schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List


# =========================================================
# SIGNUP SCHEMA
# =========================================================
class SignupSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)
    role: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str):
        allowed_roles = {"Founder", "Investor", "Student", "Analyst", "Other"}
        if v not in allowed_roles:
            raise ValueError("Invalid role selected")
        return v


# =========================================================
# LOGIN SCHEMA
# =========================================================
class LoginSchema(BaseModel):
    email: EmailStr
    password: str


# =========================================================
# ONBOARDING / USER PREFERENCES SCHEMA
# =========================================================
class PreferencesSchema(BaseModel):
    sectors: List[str]
    stages: List[str]
    geography: List[str]
    risk_level: str
    investment_size: str

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str):
        allowed_risk = {"Low", "Medium", "High"}
        if v not in allowed_risk:
            raise ValueError("Invalid risk level")
        return v

    @field_validator("sectors", "stages", "geography")
    @classmethod
    def validate_non_empty_lists(cls, v: List[str], info):
        if not v or len(v) == 0:
            raise ValueError(f"{info.field_name.replace('_', ' ').title()} cannot be empty")
        return v
