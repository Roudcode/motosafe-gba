import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

app = FastAPI()

# Permite que el frontend (localhost:5173) le pueda pedir datos a esta API (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def raiz():
    return {"mensaje": "MotoSafe GBA API funcionando"}

@app.get("/hotspots")
def obtener_hotspots():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, cluster, latitud, longitud, cantidad_siniestros, mortales, graves, nivel_riesgo
        FROM hotspots_riesgo
        ORDER BY cantidad_siniestros DESC
    """)
    resultado = cur.fetchall()
    cur.close()
    conn.close()
    return resultado