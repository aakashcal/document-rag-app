#source venv/bin/activate 
from fastapi import FastAPI

app = FastAPI()
# Root endpoint that returns a simple Hello World message
@app.get("/")
def read_root():
    return {"message": "Hello World"}