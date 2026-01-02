from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# -----------------------------
# Modelos de entrada
# -----------------------------
class Record(BaseModel):
    id: str
    start: int
    end: int

class GroupPayload(BaseModel):
    records: List[Record]

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/validate/group")
async def validate_group(payload: GroupPayload):
    errors = []

    # Ordenar por inicio
    sorted_records = sorted(payload.records, key=lambda r: r.start)

    # Detectar solapamientos
    for i in range(len(sorted_records) - 1):
        current = sorted_records[i]
        next_rec = sorted_records[i + 1]

        if current.end > next_rec.start:
            errors.append({
                "records": [current.id, next_rec.id],
                "message": f"Solapamiento entre {current.id} y {next_rec.id}"
            })

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
