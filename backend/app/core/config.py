from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_PROFILE: str = "LOCAL_DEMO"
    SECRET_KEY: str = "railsync-360-dev-secret-key-change-in-production-2026-adbms"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DATABASE_URL: str = "mysql+pymysql://railsync_user:railsync_pass@localhost:3307/railsync_db"
    TEST_DATABASE_URL: str = "sqlite+pysqlite:///:memory:"

    @property
    def get_normalized_db_url(self) -> str:
        if self.DATABASE_URL.startswith("postgres://"):
            return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return self.DATABASE_URL

    FIREBASE_DATABASE_URL: str = "https://railsync360-demo-default-rtdb.firebaseio.com/"
    FIREBASE_SERVICE_ACCOUNT_KEY: Optional[str] = None
    FIREBASE_ENABLED: bool = False

    COSMOS_ENDPOINT: str = "https://railsync-cosmos-demo.documents.azure.com:443/"
    COSMOS_KEY: Optional[str] = None
    COSMOS_DATABASE: str = "RailSyncRecords"
    COSMOS_CONTAINER: str = "RegionalBookingEvents"
    COSMOS_ENABLED: bool = False

    OUTBOX_POLL_INTERVAL_SECONDS: int = 2
    OUTBOX_BATCH_SIZE: int = 10

    class Config:
        env_file = ("../.env", ".env")
        extra = "ignore"


settings = Settings()
