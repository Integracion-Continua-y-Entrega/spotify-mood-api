from fastapi import *
from routers import users, tracks, recommendations, playlists

app = FastAPI()
app.include_router(users.router, tags=["users"])
app.include_router(tracks.router, tags=["tracks"])
app.include_router(recommendations.router, tags=["recommendations"])
app.include_router(playlists.router, tags=["playlists"])

router = APIRouter(prefix="/api/v1")
@router.get("/health")
async def get_api_health():
    return {"status": "ok"}


app.include_router(router=router)