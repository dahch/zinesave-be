from pydantic import BaseModel

class Register(BaseModel):
    email: str
    password: str
    name: str
    is_company: bool = False
    country: str | None = None
    vat_number: str | None = None


class Login(BaseModel):
    email: str
    password: str