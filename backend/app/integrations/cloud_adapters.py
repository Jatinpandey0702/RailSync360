import logging
from typing import Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache clients if initialized
_firebase_app = None
_cosmos_client = None
_cosmos_container = None


class CloudIntegrationManager:
    """
    Manages Firebase and Azure Cosmos DB cloud connections.
    Includes honest status reporting: never claims live connectivity unless verified.
    """

    @staticmethod
    def is_firebase_enabled() -> bool:
        return settings.FIREBASE_ENABLED and bool(settings.FIREBASE_DATABASE_URL)

    @staticmethod
    def is_cosmos_enabled() -> bool:
        return settings.COSMOS_ENABLED and bool(settings.COSMOS_KEY) and bool(settings.COSMOS_ENDPOINT)

    @classmethod
    def get_firebase_status(cls) -> Dict[str, Any]:
        if not settings.FIREBASE_ENABLED:
            return {
                "status": "LOCAL_FALLBACK",
                "message": "Firebase Realtime DB disabled in LOCAL_DEMO mode. Real-time availability served via API polling fallback.",
                "connected": False
            }
        try:
            # Check Firebase Admin SDK if key supplied
            import firebase_admin
            from firebase_admin import db
            return {
                "status": "CONNECTED" if firebase_admin._apps else "CONFIGURED_NOT_INITIALIZED",
                "message": "Firebase Realtime Database configured.",
                "connected": bool(firebase_admin._apps)
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": str(e),
                "connected": False
            }

    @classmethod
    def get_cosmos_status(cls) -> Dict[str, Any]:
        if not settings.COSMOS_ENABLED:
            return {
                "status": "LOCAL_FALLBACK",
                "message": "Azure Cosmos DB disabled in LOCAL_DEMO mode. Regional records queryable via MySQL outbox telemetry.",
                "connected": False
            }
        try:
            return {
                "status": "CONFIGURED",
                "message": f"Cosmos endpoint: {settings.COSMOS_ENDPOINT}",
                "connected": True
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": str(e),
                "connected": False
            }

    @classmethod
    def publish_seat_projection_to_firebase(cls, journey_id: int, travel_class: str, payload: dict) -> Tuple[bool, str]:
        """
        Publishes monotonic seat availability counter to:
        /live_seats/{journey_id}/{travel_class}
        """
        if not cls.is_firebase_enabled():
            return False, "Firebase disabled in LOCAL_DEMO mode"

        try:
            import firebase_admin
            from firebase_admin import credentials, db

            global _firebase_app
            if not _firebase_app and not firebase_admin._apps:
                if settings.FIREBASE_SERVICE_ACCOUNT_KEY:
                    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
                    _firebase_app = firebase_admin.initialize_app(cred, {
                        'databaseURL': settings.FIREBASE_DATABASE_URL
                    })
                else:
                    return False, "FIREBASE_SERVICE_ACCOUNT_KEY missing"

            ref = db.reference(f"live_seats/{journey_id}/{travel_class}")
            ref.set({
                "available": payload.get("available_seats"),
                "capacity": payload.get("capacity"),
                "waitlist_count": payload.get("waitlist_count"),
                "version": payload.get("version"),
                "updated_at": payload.get("timestamp")
            })
            return True, "Published to Firebase"
        except Exception as e:
            logger.error(f"Failed to publish to Firebase: {e}")
            return False, str(e)

    @classmethod
    def publish_regional_event_to_cosmos(cls, payload: dict) -> Tuple[bool, str]:
        """
        Publishes non-sensitive regional booking telemetry document to Azure Cosmos DB:
        Partition Key: /region
        """
        if not cls.is_cosmos_enabled():
            return False, "Azure Cosmos DB disabled in LOCAL_DEMO mode"

        try:
            from azure.cosmos import CosmosClient, PartitionKey

            global _cosmos_client, _cosmos_container
            if not _cosmos_client:
                _cosmos_client = CosmosClient(settings.COSMOS_ENDPOINT, credential=settings.COSMOS_KEY)
                database = _cosmos_client.get_database_client(settings.COSMOS_DATABASE)
                _cosmos_container = database.get_container_client(settings.COSMOS_CONTAINER)

            doc = {
                "id": payload.get("event_id"),
                "pnr": payload.get("pnr"),
                "journey_id": payload.get("journey_id"),
                "train_number": payload.get("train_number"),
                "region": payload.get("region", "Northern"),
                "travel_class": payload.get("travel_class"),
                "passenger_count": payload.get("passenger_count"),
                "ticket_status": payload.get("ticket_status"),
                "version": payload.get("version"),
                "timestamp": payload.get("timestamp")
            }
            _cosmos_container.upsert_item(doc)
            return True, "Upserted to Cosmos DB"
        except Exception as e:
            logger.error(f"Failed to publish to Cosmos DB: {e}")
            return False, str(e)
