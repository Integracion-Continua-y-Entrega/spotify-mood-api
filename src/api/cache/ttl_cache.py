import time
import asyncio
import logging
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Caché en memoria con tiempo de vida (TTL).
    
    Atributos:
        _store : diccionario interno  { key -> (value, expiry_timestamp) }
        _ttl   : segundos que vive cada entrada
        _lock  : evita que dos coroutines reconstruyan el caché al mismo tiempo
                 (problema conocido como "cache stampede")
    """

    def __init__(self, ttl_seconds: int = 3600):
        self._store: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds
        self._locks: dict[str, asyncio.Lock] = {}

    def _is_valid(self, key: str) -> bool:
        if key not in self._store:
            return False
        _, expiry = self._store[key]
        return time.monotonic() < expiry

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Un Lock por clave para no bloquear claves independientes."""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def get(self, key: str) -> Any | None:
        """Devuelve el valor si existe y es válido, si no None."""
        if self._is_valid(key):
            value, expiry = self._store[key]
            remaining = expiry - time.monotonic()
            logger.debug("Cache HIT  key='%s'  ttl_restante=%.1fs", key, remaining)
            return value
        return None

    def set(self, key: str, value: Any) -> None:
        """Guarda value bajo key con tiempo de expiración = ahora + TTL."""
        expiry = time.monotonic() + self._ttl
        self._store[key] = (value, expiry)
        logger.debug("Cache SET  key='%s'  expira en %.1fs", key, self._ttl)

    def invalidate(self, key: str) -> None:
        """Borra una entrada manualmente."""
        self._store.pop(key, None)
        logger.debug("Cache INVALIDATED  key='%s'", key)

    async def get_or_fetch(
        self,
        key: str,
        fetcher: Callable[[], Coroutine],
    ) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached

        # MISS: Al levantar por primera vez la API o tras expirar el último cache 
        async with self._get_lock(key):
            # Validación doble por si una solicitud ya hizo la llamada
            cached = self.get(key)
            if cached is not None:
                logger.debug("Cache HIT (post-lock) key='%s'", key)
                return cached

            # Fetch a la bd
            logger.info("Cache MISS  key='%s' — consultando BD...", key)
            value = await fetcher()
            self.set(key, value)
            return value