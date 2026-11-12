from fastapi import APIRouter
router = APIRouter(tags=["system"])

@router.get("/health")
def health_check():
    return {
        "status": "Healthy",
        "message": "Enterprise Revenue Operations AI Agent is running"
    }

@router.get("/about")
def about_application():
        return {
        "application": "Enterprise Revenue Operations AI Agent",
        "version": "1.0.0",
        "purpose": "Business automation"
    }