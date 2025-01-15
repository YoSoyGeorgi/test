from pydantic import BaseModel
from typing import Optional, Dict, Any

class ErrorResponse(BaseModel):
    status: int
    type: str
    error: str
    message: str

class SuccessResponse(BaseModel):
    status: int
    type: str
    message: str
    data: Dict[str, Any]

class PDFResponseDTO(BaseModel):
    errorResponse: Optional[ErrorResponse] = None
    successResponse: Optional[SuccessResponse] = None

class Config:
    # Excluir campos con valor None en la respuesta JSON
    exclude_none = True