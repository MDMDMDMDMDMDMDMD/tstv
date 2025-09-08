from app.crud.base import CRUDBase
from app.models.file import File
from app.schemas.file import FileCreate, FileUpdate

class CRUDFile(CRUDBase[File, FileCreate, FileUpdate]):
    pass

file = CRUDFile(File)
