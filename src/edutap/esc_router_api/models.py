from typing import Annotated
from annotated_types import Ge, Le
from datetime import datetime
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import UUID4
from pydantic_extra_types.phone_numbers import PhoneNumber


AllowedAcademicLevel = Annotated[int, Ge(6), Le(8)]
AllowedCardType = Annotated[int, Ge(1), Le(4)]


class Student(BaseModel):
    europeanStudentIdentifier: str
    picInstitutionCode: int
    emailAddress: EmailStr
    expiryData: datetime
    name: str | None = None
    phoneNumbe: PhoneNumber | None = None
    academicLevel: AllowedAcademicLevel | None = None


class Card(BaseModel):
    europeanStudentCardNumber: UUID4
    cardType: AllowedCardType | None
    cardUid: str | None
