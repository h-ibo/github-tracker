from fastapi import FastAPI

app = FastAPI(title="GitHub Tracker API")

@app.get("/")
def root():
    return {"message": "Ayakta ve çalışıyor"}