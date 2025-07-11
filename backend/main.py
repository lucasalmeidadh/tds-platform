# backend/main.py
import os
import json
import google.generativeai as genai
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

# Importações locais dos nossos arquivos
from . import models, schemas
from .database import SessionLocal, create_db_and_tables

# Carrega as variáveis de ambiente (do arquivo .env na raiz)
load_dotenv()

# --- Configuração do Gemini ---
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("API do Gemini configurada com sucesso.")
except Exception as e:
    print(f"ERRO: Não foi possível configurar a API do Gemini. Verifique sua GOOGLE_API_KEY. Erro: {e}")
    model = None

# --- Configuração da API FastAPI ---
app = FastAPI(title="TDS Platform API")

# Middleware para permitir que o frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite todas as origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Evento de inicialização: cria a tabela no banco quando a API sobe
@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()
    print("Banco de dados conectado e tabelas criadas (se não existiam).")

# Dependência para obter uma sessão do banco de dados
async def get_db():
    async with SessionLocal() as db:
        yield db

# --- Endpoints da API ---

@app.get("/")
def read_root():
    return {"status": "API da TDS Platform no ar!", "database_connection": "OK"}

@app.post("/api/v1/analyze", response_model=schemas.InteractionResponse)
async def analyze_text(request_body: schemas.TextToAnalyze, db: AsyncSession = Depends(get_db)):
    if not model:
        raise HTTPException(status_code=500, detail="API do Gemini não configurada.")
    
    text_to_analyze = request_body.text
    prompt = f"""
    Aja como um especialista em análise de feedback de clientes.
    Analise o seguinte texto e retorne APENAS um JSON válido com a estrutura:
    {{"sentimento": "Positivo | Neutro | Negativo", "resumo": "Um resumo curto do feedback em uma frase.", "sugestao_de_resposta": "Uma sugestão de resposta profissional e empática para o cliente."}}

    Texto para analisar: "{text_to_analyze}"
    """
    
    response = model.generate_content(prompt)
    clean_response_text = response.text.strip().replace('```json', '').replace('```', '')
    analysis_data = json.loads(clean_response_text)
    
    new_interaction = models.Interaction(
        original_text=text_to_analyze,
        sentiment=analysis_data.get("sentimento"),
        summary=analysis_data.get("resumo"),
        suggested_response=analysis_data.get("sugestao_de_resposta")
    )
    
    db.add(new_interaction)
    await db.commit()
    await db.refresh(new_interaction)
    return new_interaction

@app.get("/api/v1/interactions", response_model=list[schemas.InteractionResponse])
async def get_all_interactions(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(models.Interaction).order_by(models.Interaction.created_at.desc()))
    interactions = result.scalars().all()
    return interactions

# --- NOVO ENDPOINT DE CONSULTA INTELIGENTE ---

@app.post("/api/v1/query")
async def query_product_stock(request_body: schemas.QueryRequest, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, or_

    if not model:
        raise HTTPException(status_code=500, detail="API do Gemini não configurada.")

    user_question = request_body.question

    # 1. Primeiro, pedimos ao Gemini para extrair o nome ou código do produto da pergunta.
    identifier_prompt = f"""
    Da pergunta do usuário a seguir, extraia apenas o nome, código ou referência principal do produto.
    Retorne SOMENTE o identificador do produto, sem nenhuma palavra extra.
    Pergunta: "{user_question}"
    """
    identifier_response = model.generate_content(identifier_prompt)
    product_identifier = identifier_response.text.strip()

    # 2. Agora, buscamos no banco de dados por esse identificador.
    # O 'ilike' faz uma busca insensível a maiúsculas/minúsculas.
    query = select(models.Product).where(
        models.Product.product_deleted == False, # Garante que não vamos buscar produtos deletados
        or_(
            models.Product.product_code.ilike(f'%{product_identifier}%'),
            models.Product.product_description.ilike(f'%{product_identifier}%'),
            models.Product.product_reference.ilike(f'%{product_identifier}%')
        )
    )
    result = await db.execute(query)
    product = result.scalars().first()

    # 3. Se não encontrarmos o produto, avisamos.
    if not product:
        return {"answer": f"Desculpe, não consegui encontrar um produto correspondente a '{product_identifier}' em nosso sistema."}

    # 4. Se encontramos, pedimos ao Gemini para formular uma resposta amigável.
    answer_prompt = f"""
    Você é um assistente de vendas da TDS Autopeças.
    O cliente perguntou sobre o estoque de um produto. Use as informações abaixo para responder.
    - Nome do Produto: {product.product_description}
    - Estoque Atual: {product.product_balance} unidades

    Formule uma resposta clara, direta e amigável em português para o cliente.
    """
    final_answer_response = model.generate_content(answer_prompt)

    return {"answer": final_answer_response.text}
