from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# liberar acesso frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARQUIVO = "memoria_qa.json"

def carregar():
    if not os.path.exists(ARQUIVO):
        return {"correcoes": {}, "estrategias": {}, "historico": []}

    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/")
def home():
    return {"status": "QA Brain rodando 🚀"}


@app.get("/memoria")
def memoria():
    return carregar()


@app.get("/estrategias")
def estrategias():
    return carregar().get("estrategias", {})


@app.get("/historico")
def historico():
    return carregar().get("historico", [])


@app.get("/stats")
def stats():
    data = carregar()

    total = len(data["historico"])
    sucesso = sum(1 for x in data["historico"] if x["sucesso"] == 1)

    taxa = (sucesso / total * 100) if total > 0 else 0

    return {
        "total_execucoes": total,
        "sucessos": sucesso,
        "taxa_sucesso": round(taxa, 2)
    }