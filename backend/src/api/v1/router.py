from fastapi import APIRouter

api_router = APIRouter()

# Import and include all endpoint routers
from .endpoints import auth, test, users, tokens

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# Also expose login/register at /api/v1 without /auth for tests expecting that path
api_router.include_router(auth.router, prefix="", tags=["Authentication"])
api_router.include_router(test.router, prefix="/test", tags=["Test"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(tokens.router, prefix="", tags=["Tokens"])