# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

import json
import secrets
from typing import Any, List, Dict, Union
from pydantic import Field, AliasChoices, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=(".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    MASTER_BOT_TOKEN: str = Field(
        default="1234567890:TEST_MASTER_BOT_TOKEN_PLACEHOLDER",
        validation_alias=AliasChoices("MASTER_BOT_TOKEN", "BOT_TOKEN"),
        description="Bot token for Master Bot",
    )
    DELIVERY_BOT_TOKEN: str = Field(
        default="",
        validation_alias=AliasChoices("DELIVERY_BOT_TOKEN", "DELIVERY_TOKEN"),
        description="Bot token for Delivery Bot (optional: if omitted or same as master, Master Bot handles deliveries directly)",
    )

    MASTER_BOT_USERNAME: str = Field(
        default="",
        description="Telegram username of Master Bot",
    )
    DELIVERY_BOT_USERNAME: str = Field(
        default="",
        description="Telegram username of Delivery Bot",
    )

    AUTO_DELETE_FILE_SECONDS: int = Field(
        default=300,
        description="Duration before sent files are automatically deleted from user DM",
    )

    BOT_TYPE: str = Field(
        default="porn",
        validation_alias=AliasChoices("BOT_TYPE", "BOT_SKIN", "SKIN"),
        description="Bot personality",
    )

    OWNER_IDS: List[int] = Field(
        default_factory=lambda: [7467775243],
        validation_alias=AliasChoices("OWNER_IDS", "OWNER_ID", "SUDO_USERS"),
        description="List of integer Telegram User IDs for system owners",
    )

    MONGO_URI: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices("MONGO_URI", "MONGO_DB", "MONGODB_URI"),
        description="MongoDB connection URI",
    )
    DATABASE_NAME: str = Field(
        default="telegram_file_bot",
        validation_alias=AliasChoices("DATABASE_NAME", "MONGODB_DB_NAME"),
        description="MongoDB database name",
    )

    LOGGER_GROUP_ID: int = Field(
        default=int,
        validation_alias=AliasChoices("LOGGER_GROUP_ID", "LOGGER_GROUP"),
        description="Private group ID for manifest db.json and user requests",
    )
    FILES_GROUP_ID: int = Field(
        default=-1009876543210,
        validation_alias=AliasChoices("FILES_GROUP_ID", "DATABASE_CHANNEL"),
        description="Private group ID where source files are uploaded",
    )
    MANIFEST_DEBOUNCE_MINUTES: int = Field(
        default=30,
        ge=1,
        description="Minutes to wait after last uploaded file before publishing updated manifest db.json",
    )

    SUBSCRIBE: List[Union[str, int]] = Field(
        default_factory=list,
        description="List of channel usernames (@channel) or IDs (-100...)",
    )
    SUBSCRIBE_INVITE_LINKS: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of private channel IDs to join invite URLs",
    )
    START_IMAGE_URL: str = Field(
        default="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&q=80",
        description="Image CDN URL for start and help messages",
    )
    SUPPORT_GROUP_URL: str = Field(
        default="https://t.me/social_bots",
        description="Support group invite URL",
    )
    BACKUP_CHANNEL_URL: str = Field(
        default="https://t.me/social_bots",
        description="Backup channel invite URL",
    )

    SEARCH_PAGE_SIZE: int = Field(default=10, ge=1, le=50)
    SEARCH_CACHE_SIZE: int = Field(default=1000, ge=10, le=100000)
    SEARCH_STRICT_AND: bool = Field(default=True)
    SEARCH_FUZZY_ENABLED: bool = Field(default=True)
    SEARCH_FUZZY_THRESHOLD: int = Field(default=75, ge=40, le=100)

    TOKEN_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        min_length=32,
    )
    TOKEN_EXPIRY_SECONDS: int = Field(default=0, ge=0)

    RATE_LIMIT_BURST: int = Field(default=5, ge=1)
    RATE_LIMIT_RATE: float = Field(default=1.0, ge=0.1)

    WEB_SERVER_HOST: str = Field(default="0.0.0.0")
    WEB_SERVER_PORT: int = Field(default=8080, ge=1, le=65535)
    WEBHOOK_ENABLED: bool = Field(default=False)
    WEBHOOK_BASE_URL: str = Field(default="")
    WEBHOOK_SECRET: str = Field(default="")

    LOG_LEVEL: str = Field(default="INFO")

    @field_validator("OWNER_IDS", mode="before")
    @classmethod
    def parse_owner_ids(cls, v: Any) -> List[int]:
        if isinstance(v, int):
            return [v]
        elif isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    return [int(x) for x in json.loads(v)]
                except Exception:
                    pass
            return [int(p.strip()) for p in v.split(",") if p.strip()]
        elif isinstance(v, (list, tuple, set)):
            return [int(x) for x in v]
        raise ValueError("Invalid format for OWNER_IDS")

    @field_validator("SUBSCRIBE", mode="before")
    @classmethod
    def parse_subscribe(cls, v: Any) -> List[Union[str, int]]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            parts = [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, (list, tuple)):
            parts = v
        else:
            return []

        res: List[Union[str, int]] = []
        for x in parts:
            try:
                res.append(int(x))
            except ValueError:
                s = str(x).strip()
                res.append(s if s.startswith("@") else f"@{s}")
        return res

    @field_validator("SUBSCRIBE_INVITE_LINKS", mode="before")
    @classmethod
    def parse_invite_links(cls, v: Any) -> Dict[str, str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return {}
            try:
                return json.loads(v)
            except Exception:
                return {}
        elif isinstance(v, dict):
            return {str(k): str(val) for k, val in v.items()}
        return {}

    @model_validator(mode="after")
    def validate_rules(self) -> Settings:
        for oid in self.OWNER_IDS:
            if oid <= 0:
                raise ValueError(f"Owner ID must be a positive integer, got: {oid}")

        if self.WEBHOOK_ENABLED:
            if not self.WEBHOOK_BASE_URL:
                raise ValueError("WEBHOOK_BASE_URL is required when WEBHOOK_ENABLED is True")
            if not self.WEBHOOK_BASE_URL.startswith("https://"):
                raise ValueError("WEBHOOK_BASE_URL must begin with https:// for Telegram webhooks")
            if not self.WEBHOOK_SECRET:
                raise ValueError("WEBHOOK_SECRET is required when WEBHOOK_ENABLED is True")

        return self

    @property
    def is_dual_bot(self) -> bool:
        return bool(self.DELIVERY_BOT_TOKEN and self.DELIVERY_BOT_TOKEN != self.MASTER_BOT_TOKEN)

    @property
    def delivery_username(self) -> str:
        if self.is_dual_bot and self.DELIVERY_BOT_USERNAME:
            return self.DELIVERY_BOT_USERNAME
        return self.MASTER_BOT_USERNAME or self.DELIVERY_BOT_USERNAME or ""

    def is_owner(self, user_id: int) -> bool:
        return user_id in self.OWNER_IDS

    def __repr__(self) -> str:
        return (
            f"<Settings master_bot=@{self.MASTER_BOT_USERNAME or 'pending'} "
            f"delivery_bot=@{self.DELIVERY_BOT_USERNAME or 'pending'} "
            f"database={self.DATABASE_NAME} "
            f"owners_count={len(self.OWNER_IDS)}>"
        )

settings = Settings()
