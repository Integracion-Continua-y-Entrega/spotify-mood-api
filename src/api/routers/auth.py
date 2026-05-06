
from fastapi import APIRouter, Depends

from services.track_service import TrackService
from services.user_service import UserService
from dependencies import get_auth_service, get_user_service, get_track_service
from models.login_payload import LoginPayload
from services.auth_service import AuthService

router = APIRouter()


@router.post(
    path="/login") 
async def spotify_login(payload: LoginPayload, auth_service: AuthService = Depends(get_auth_service), user_service: UserService = Depends(get_user_service), track_service: TrackService = Depends(get_track_service)):
    return await auth_service.spotify_login(payload=payload, user_service=user_service, track_service=track_service)
