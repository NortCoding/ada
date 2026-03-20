from fastapi import FastAPI

app = FastAPI(title="ALMA Agent", version="0.1.0")

@app.get("/health")
def health():
    return {"agent": "ALMA", "status": "ready"}

@app.get("/")
def root():
    return {"agent": "ALMA", "message": "Agent active"}
