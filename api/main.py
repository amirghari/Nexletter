from fastapi import FastAPI
from api.routes import router

app = FastAPI()

app.include_router(router)

# Optional root
@app.get("/")
def root():
    return {"message": "NeXletter API is up!"}