# backend/schemas.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

# --- Esquemas de Interação (Análise de Texto) ---
class TextToAnalyze(BaseModel):
    text: str

class InteractionResponse(BaseModel):
    id: int
    original_text: str
    sentiment: Optional[str]
    summary: Optional[str]
    suggested_response: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# --- Esquemas de Produto ---
class QueryRequest(BaseModel):
    question: str

class ProductResponse(BaseModel):
    product_id: int
    product_description: str
    product_balance: int
    class Config:
        from_attributes = True

# --- Esquemas de Usuário ---
class UserBase(BaseModel):
    user_email: EmailStr
    user_name: str
    user_branchid: int
    user_role: str = 'vendedor'

class UserCreate(UserBase):
    password: str

class User(UserBase):
    user_id: int
    user_deleted: bool
    user_createdat: datetime
    class Config:
        from_attributes = True

# --- Esquemas de Mensagem e Conversa ---
class MessageBase(BaseModel):
    message_content: str
    message_sender_type: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    message_id: int
    message_sentat: datetime
    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    customer_whatsapp_id: str
    conversation_status: str = 'aberta'
    assigned_userid: Optional[int] = None

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    conversation_id: int
    conversation_createdat: datetime
    messages: List[Message] = [] # Inclui as mensagens dentro da conversa
    class Config:
        from_attributes = True