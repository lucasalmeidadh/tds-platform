# backend/main.py
import os
import json
import httpx
import google.generativeai as genai
import unicodedata  # <--- ADICIONADO para remover acentos
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_  # <--- ADICIONADO 'and_' para a busca
from dotenv import load_dotenv

# Importações locais
from . import models
from .database import SessionLocal, create_db_and_tables

load_dotenv()

# --- Configurações ---
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

app = FastAPI(title="TDS Platform API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Funções de Ciclo de Vida e Dependências ---

@app.on_event("startup")
async def on_startup():
    """Cria as tabelas do banco de dados ao iniciar a aplicação."""
    await create_db_and_tables()
    print("Banco de dados conectado e tabelas criadas.")

async def get_db():
    """
    Dependência do FastAPI para gerenciar a sessão do banco de dados.
    Abre uma sessão, executa a lógica da rota, faz commit ou rollback, e fecha a sessão.
    """
    db = SessionLocal()
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()

# --- Funções Auxiliares ---

def remove_accents(input_str: str) -> str:
    """Normaliza uma string, removendo acentos e convertendo para minúsculas."""
    if not isinstance(input_str, str):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode('ASCII').lower()

async def send_whatsapp_message(to: str, message: str):
    """Envia uma mensagem de texto para um número via API do WhatsApp."""
    url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message},
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()  # Lança exceção para erros 4xx/5xx
            print(f"Mensagem enviada com sucesso para {to}")
        except httpx.HTTPStatusError as e:
            print(f"Falha ao enviar mensagem: {e.response.status_code}")
            print(f"Resposta da API: {e.response.json()}")
        except Exception as e:
            print(f"Um erro inesperado ocorreu ao enviar a mensagem: {e}")

# --- Lógica Principal de Resposta ---

async def get_product_info_and_respond(user_question: str, db: AsyncSession):
    """
    Lógica completa para processar a pergunta do usuário, buscar no banco e formular uma resposta.
    """
    # 1. Extrai o identificador do produto da pergunta usando o Gemini
    identifier_prompt = f"""
    Da pergunta do usuário a seguir, extraia apenas o nome, código ou referência principal do produto.
    Se a pergunta for um cumprimento ou não contiver um produto claro, retorne exatamente a string "N/A".
    Retorne SOMENTE o identificador do produto ou "N/A".
    Pergunta: "{user_question}"
    """
    identifier_response = model.generate_content(identifier_prompt)
    product_identifier = identifier_response.text.strip()

    # Se for um cumprimento ou não houver produto, responde de forma genérica
    if product_identifier == "N/A":
        final_answer = "Olá! Sou o assistente virtual da TDS Autopeças. Como posso te ajudar a encontrar as peças ou serviços que você precisa?"
    else:
        # 2. Lógica de Busca Inteligente no Banco de Dados
        search_terms = remove_accents(product_identifier).split()
        conditions = []
        for term in search_terms:
            conditions.append(
                or_(
                    models.Product.product_code.ilike(f'%{term}%'),
                    models.Product.product_description.ilike(f'%{term}%'),
                    models.Product.product_reference.ilike(f'%{term}%')
                )
            )
        
        query = select(models.Product).where(
            models.Product.product_deleted == False,
            and_(*conditions)
        )
        
        result = await db.execute(query)
        product = result.scalars().first()

        # 3. Formula a resposta final com base no resultado da busca
        if not product:
            final_answer = f"Desculpe, não consegui encontrar um produto correspondente a '{product_identifier}' em nosso sistema."
        else:
            answer_prompt = f"""
            Você é um assistente de vendas da TDS Autopeças. O cliente perguntou sobre um produto.
            Use as informações abaixo para responder de forma clara e amigável.
            - Nome do Produto: {product.product_description}
            - Preço Atual: R$ {product.product_price}
            - Estoque Atual: {product.product_balance} unidades
            """
            final_answer_response = model.generate_content(answer_prompt)
            final_answer = final_answer_response.text

    # 4. Salva a interação no banco de dados
    # O `db.commit()` foi removido daqui, pois a dependência `get_db` já cuida disso.
    new_interaction = models.Interaction(
        original_text=user_question,
        sentiment="Consulta de Produto" if product_identifier != "N/A" else "Saudação",
        summary=f"Busca por: '{product_identifier}'" if product_identifier != "N/A" else "N/A",
        suggested_response=final_answer
    )
    db.add(new_interaction)
    
    return final_answer

# --- Endpoints da API ---

@app.get("/")
def read_root():
    """Endpoint raiz para verificar se a API está no ar."""
    return {"status": "API da TDS Platform no ar!", "database_connection": "OK"}

# Em backend/main.py

@app.get("/api/v1/webhook")
def verify_webhook(request: Request):
    """Endpoint para verificação do Webhook do WhatsApp (GET)."""
    # LINHA DE DEPURAÇÃO ADICIONADA AQUI
    print(f"TOKEN ESPERADO PELO CÓDIGO: '{WHATSAPP_VERIFY_TOKEN}'") 
    
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        print("WEBHOOK VERIFICADO COM SUCESSO!")
        return int(challenge)
    
    print("FALHA NA VERIFICAÇÃO DO WEBHOOK. Tokens não correspondem.")
    # Adicione um print para ver o token que a Meta está enviando
    print(f"Token recebido da Meta: '{token}'") 
    raise HTTPException(status_code=403, detail="Falha na verificação do token.")

@app.post("/api/v1/webhook")
async def receive_message(request: Request, db: AsyncSession = Depends(get_db)):
    """Endpoint que recebe as notificações de mensagens do WhatsApp (POST)."""
    body = await request.json()
    print("Payload recebido do WhatsApp:")
    print(json.dumps(body, indent=2))

    try:
        # Extrai o corpo da mensagem e o ID do remetente
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        message_body = message['text']['body']
        sender_id = message['from']
        
        # Chama a função principal para obter a resposta
        response_text = await get_product_info_and_respond(message_body, db)

        # Envia a resposta de volta para o usuário
        await send_whatsapp_message(sender_id, response_text)

    except (KeyError, IndexError) as e:
        # Ignora notificações que não são mensagens de texto padrão
        print(f"Notificação ignorada (não é uma mensagem de texto do usuário ou formato inesperado): {e}")

    return {"status": "ok"}