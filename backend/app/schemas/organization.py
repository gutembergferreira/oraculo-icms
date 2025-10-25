from app.schemas.base import OraculoBaseModel


class OrganizationCreate(OraculoBaseModel):
    name: str
    cnpj: str
    slug: str


class OrganizationRead(OraculoBaseModel):
    id: int
    name: str
    cnpj: str
    slug: str
    zfm_enabled: bool
