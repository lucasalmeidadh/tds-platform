from pydantic import BaseModel
from datetime import datetime

# Esquema para o corpo da requisição de análise
class TextToAnalyze(BaseModel):
    text: str

# Esquema para exibir uma interação salva
class InteractionResponse(BaseModel):
    id: int
    original_text: str
    sentiment: str | None
    summary: str | None
    suggested_response: str | None
    created_at: datetime

    class Config:
        from_attributes = True # Permite que o Pydantic leia dados de objetos do SQLAlchemy