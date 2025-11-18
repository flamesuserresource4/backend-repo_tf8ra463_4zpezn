import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ----- Universe of Decisions API -----

class CompletePayload(BaseModel):
    user_id: str
    satellite_id: int
    completed: bool = True


# Static content for satellites (textual detail + a simple reflective prompt)
SATELLITES: List[dict] = [
    {
        "id": 1,
        "title": "1. El Poder de Decidir",
        "question": "¿Somos realmente dueños de nuestras elecciones o actuamos en piloto automático más de lo que creemos?",
        "chips": ["Autonomía", "Hábitos", "Atención"],
        "detail": "Explora cómo la intención consciente compite con los hábitos y las señales del entorno. Pequeñas pausas de conciencia pueden cambiar trayectorias completas.",
        "activity": "Describe una micro-decisión de hoy que vas a tomar con plena atención.",
    },
    {
        "id": 2,
        "title": "2. Cerebro y Emoción",
        "question": "¿Cómo dialogan razón y emoción al decidir, y quién tiene la última palabra?",
        "chips": ["Sistema 1 & 2", "Interocepción", "Regulación"],
        "detail": "La emoción filtra la información antes de la lógica. No hay decisiones 'puras'; aprende a regular para decidir mejor.",
        "activity": "Nombra una emoción reciente que influyó tu última decisión importante.",
    },
    {
        "id": 3,
        "title": "3. Decisiones en Contexto",
        "question": "¿Cuánto pesa el entorno (social, cultural, digital) en lo que elegimos?",
        "chips": ["Normas", "Arquitectura de elección", "Influencias"],
        "detail": "Diseña tu entorno para facilitar buenas opciones: lo cercano, visible y fácil gana.",
        "activity": "Anota un cambio de entorno que harías para facilitar una mejor elección.",
    },
    {
        "id": 4,
        "title": "4. Integridad y Dilema",
        "question": "¿Qué sacrificamos (y por qué) cuando las opciones chocan con nuestros valores?",
        "chips": ["Valores", "Costes ocultos", "Coraje"],
        "detail": "Clarificar valores reduce fricción en dilemas. Anticipa tus líneas rojas antes del momento crítico.",
        "activity": "Escribe un valor no negociable y una acción que lo honre esta semana.",
    },
    {
        "id": 5,
        "title": "5. Sesgos y Atajos",
        "question": "¿Qué sesgos invisibles guían nuestros atajos mentales al decidir?",
        "chips": ["Anclaje", "Confirmación", "Disponibilidad"],
        "detail": "Detectar sesgos no los elimina, pero reduce su poder cuando introduces fricción consciente.",
        "activity": "Señala un sesgo que pudiste haber tenido en una elección reciente.",
    },
    {
        "id": 6,
        "title": "6. Impacto y Futuro",
        "question": "¿Cómo cambia el futuro cuando hoy decidimos distinto?",
        "chips": ["Efecto compuesto", "Trayectorias", "Aprendizaje"],
        "detail": "Las micro-decisiones diarias acumulan efectos exponenciales. Define tu dirección, no solo el siguiente paso.",
        "activity": "Esboza una micro-acción diaria que, repetida, cambiaría tu año.",
    },
]


@app.get("/api/satellites")
def get_satellites():
    return {"items": SATELLITES}


@app.get("/api/progress/{user_id}")
def get_progress(user_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    doc = db["progress"].find_one({"user_id": user_id})
    if not doc:
        # create new progress doc
        create_document("progress", {"user_id": user_id, "completed": []})
        return {"user_id": user_id, "completed": []}
    return {"user_id": user_id, "completed": doc.get("completed", [])}


@app.post("/api/progress/complete")
def mark_complete(payload: CompletePayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    doc = db["progress"].find_one({"user_id": payload.user_id})
    if not doc:
        create_document("progress", {"user_id": payload.user_id, "completed": []})
        doc = db["progress"].find_one({"user_id": payload.user_id})

    completed: List[int] = doc.get("completed", [])

    if payload.completed:
        if payload.satellite_id not in completed:
            completed.append(payload.satellite_id)
    else:
        completed = [sid for sid in completed if sid != payload.satellite_id]

    db["progress"].update_one({"_id": doc["_id"]}, {"$set": {"completed": completed}})
    return {"user_id": payload.user_id, "completed": completed}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
