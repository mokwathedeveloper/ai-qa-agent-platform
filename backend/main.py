from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI QA Agent Platform API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
