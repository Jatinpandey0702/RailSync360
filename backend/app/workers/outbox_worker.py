import time
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.entities import BookingEvent
from app.integrations.cloud_adapters import CloudIntegrationManager

logger = logging.getLogger(__name__)


def process_outbox_batch(db: Session, batch_size: int = 10) -> int:
    """
    Polls pending events from booking_events table and dispatches them to
    Firebase Realtime Database and Azure Cosmos DB.
    Tracks success and errors per destination independently.
    """
    pending_events = (
        db.query(BookingEvent)
        .filter((BookingEvent.firebase_synced == False) | (BookingEvent.cosmos_synced == False))
        .order_by(BookingEvent.id.asc())
        .limit(batch_size)
        .all()
    )

    if not pending_events:
        return 0

    processed_count = 0
    for event in pending_events:
        event.attempts += 1
        payload = event.payload or {}

        # 1. Sync to Firebase if needed
        if not event.firebase_synced:
            if CloudIntegrationManager.is_firebase_enabled():
                journey_id = payload.get("journey_id")
                travel_class = payload.get("travel_class")
                if journey_id and travel_class:
                    success, msg = CloudIntegrationManager.publish_seat_projection_to_firebase(
                        journey_id, travel_class, payload
                    )
                    if success:
                        event.firebase_synced = True
                        event.firebase_error = None
                    else:
                        event.firebase_error = msg
            else:
                # In LOCAL_DEMO mode, mark synced locally so queue doesn't block
                event.firebase_synced = True
                event.firebase_error = "Skipped (LOCAL_DEMO mode)"

        # 2. Sync to Azure Cosmos DB if needed
        if not event.cosmos_synced:
            if CloudIntegrationManager.is_cosmos_enabled():
                success, msg = CloudIntegrationManager.publish_regional_event_to_cosmos(payload)
                if success:
                    event.cosmos_synced = True
                    event.cosmos_error = None
                else:
                    event.cosmos_error = msg
            else:
                # In LOCAL_DEMO mode, mark synced locally
                event.cosmos_synced = True
                event.cosmos_error = "Skipped (LOCAL_DEMO mode)"

        if event.firebase_synced and event.cosmos_synced:
            event.processed_at = datetime.utcnow()

        processed_count += 1

    db.commit()
    return processed_count


def run_outbox_worker_loop():
    """
    Continuous worker loop for processing outbox events.
    """
    logger.info("Starting RailSync 360 Outbox Worker...")
    while True:
        db = SessionLocal()
        try:
            processed = process_outbox_batch(db, batch_size=settings.OUTBOX_BATCH_SIZE)
            if processed > 0:
                logger.info(f"Processed {processed} outbox event(s).")
        except Exception as e:
            logger.error(f"Error in outbox worker: {e}")
        finally:
            db.close()
        time.sleep(settings.OUTBOX_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_outbox_worker_loop()
