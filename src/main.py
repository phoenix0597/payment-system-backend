from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.routes import auth, users, payments, accounts
from src.config.config import settings

app = FastAPI(title="Payment System API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_PREFIX + "/auth", tags=["auth"])
app.include_router(users.router, prefix=settings.API_PREFIX + "/users", tags=["users"])
app.include_router(
    payments.router, prefix=settings.API_PREFIX + "/payments", tags=["payments"]
)


app.include_router(
    accounts.router, prefix=settings.API_PREFIX + "/accounts", tags=["accounts"]
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
