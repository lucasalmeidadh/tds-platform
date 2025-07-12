# backend/models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.sql import func
from .database import Base

# --- Tabela de Interações com a IA ---
class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    sentiment = Column(String)
    summary = Column(Text)
    suggested_response = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# --- Tabela de Filiais ---
# Assumindo que você já tem a classe para a tabela 'branch'
# Se não tiver, pode adicionar aqui. Exemplo:
# class Branch(Base):
#     __tablename__ = "branch"
#     branch_id = Column(Integer, primary_key=True)
#     ... (outras colunas)

# --- Tabela de Produtos ---
class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True)
    product_branchid = Column(Integer, ForeignKey("branch.branch_id"), nullable=False)
    product_code = Column(String(255), unique=True, nullable=False)
    product_reference = Column(String(255))
    product_description = Column(Text, nullable=False)
    product_barcode1 = Column(String(100))
    product_barcode2 = Column(String(100))
    product_brand = Column(String(100))
    product_section = Column(String(100))
    product_balance = Column(Integer, nullable=False, default=0)
    product_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    product_averagecost = Column(Numeric(10, 2), nullable=False, default=0.00)
    product_deleted = Column(Boolean, nullable=False, default=False)
    product_createdat = Column(DateTime(timezone=True), server_default=func.now())
    product_updatedat = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# --- Tabela de Usuários ---
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    user_branchid = Column(Integer, ForeignKey("branch.branch_id"), nullable=False)
    user_name = Column(String(255), nullable=False)
    user_email = Column(String(255), unique=True, nullable=False, index=True)
    user_password_hash = Column(String(255), nullable=False)
    user_role = Column(String(50), nullable=False, default='vendedor')
    user_deleted = Column(Boolean, nullable=False, default=False)
    user_createdat = Column(DateTime(timezone=True), server_default=func.now())
    user_updatedat = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# --- Tabela de Conversas ---
class Conversation(Base):
    __tablename__ = "conversations"
    conversation_id = Column(Integer, primary_key=True)
    customer_whatsapp_id = Column(String(50), nullable=False, index=True)
    assigned_userid = Column(Integer, ForeignKey("users.user_id"))
    conversation_status = Column(String(50), nullable=False, default='aberta', index=True)
    conversation_createdat = Column(DateTime(timezone=True), server_default=func.now())
    conversation_updatedat = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# --- Tabela de Mensagens ---
class Message(Base):
    __tablename__ = "messages"
    message_id = Column(Integer, primary_key=True) # Usei Integer, mas BIGINT é uma opção se o volume for extremo
    message_conversationid = Column(Integer, ForeignKey("conversations.conversation_id"), nullable=False, index=True)
    message_sender_type = Column(String(20), nullable=False) # 'cliente' ou 'vendedor'
    message_content = Column(Text, nullable=False)
    message_sentat = Column(DateTime(timezone=True), server_default=func.now())

