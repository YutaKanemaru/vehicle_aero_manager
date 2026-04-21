from fastapi import APIRouter

from app.api.v1 import auth, templates, geometries, assemblies, configurations, systems

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(geometries.router, prefix="/geometries", tags=["geometries"])
api_router.include_router(assemblies.router, prefix="/assemblies", tags=["assemblies"])
api_router.include_router(configurations.router, prefix="", tags=["cases", "runs"])
api_router.include_router(systems.router, prefix="", tags=["systems"])
