"""Shared enumerations referenced across the product.

These mirror the workflow and data contracts in the product plan (sections
7.1, 8.2, 8.5 and related). Using :class:`enum.StrEnum` keeps the values
stable at the API boundary.
"""

from __future__ import annotations

from enum import StrEnum


class WorkflowState(StrEnum):
    """Top-level project workflow states (plan section 7.1)."""

    DRAFT = "DRAFT"
    DATA_IMPORTED = "DATA_IMPORTED"
    DATA_VALIDATED = "DATA_VALIDATED"
    INSIGHTS_GENERATED = "INSIGHTS_GENERATED"
    INSIGHTS_REVIEWED = "INSIGHTS_REVIEWED"
    PRODUCT_FACTS_CONFIRMED = "PRODUCT_FACTS_CONFIRMED"
    LISTING_GENERATED = "LISTING_GENERATED"
    CREATIVES_GENERATED = "CREATIVES_GENERATED"
    COMPLIANCE_CHECKED = "COMPLIANCE_CHECKED"
    READY_FOR_EXPORT = "READY_FOR_EXPORT"
    EXPORTED = "EXPORTED"


#: Valid transitions from any state. Import moves a DRAFT project forward.
PROJECT_STATE_ORDER: tuple[WorkflowState, ...] = tuple(WorkflowState)


class FreshnessStatus(StrEnum):
    """Freshness of an observed market-data field (plan section 8.5)."""

    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    UNKNOWN = "unknown"


class SourceType(StrEnum):
    """Data source hierarchy (plan section 8.2)."""

    SYNTHETIC = "synthetic"  # L0
    USER_UPLOAD = "user_upload"  # L1
    THIRD_PARTY = "third_party"  # L2
    SP_API = "sp_api"  # L3


class EntityKind(StrEnum):
    """Kind of canonical record an import produces."""

    PRODUCT_CANDIDATE = "product_candidate"
    PRODUCT_VARIANT = "product_variant"
    REVIEW = "review"


class ImportStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportTarget(StrEnum):
    PRODUCTS = "products"
    REVIEWS = "reviews"


class AuditAction(StrEnum):
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_STATUS_CHANGED = "project.status_changed"
    IMPORT_CREATED = "import.created"
    IMPORT_PREVIEWED = "import.previewed"
    IMPORT_COMPLETED = "import.completed"
    IMPORT_FAILED = "import.failed"
    INSIGHT_GENERATED = "insight.generated"
    INSIGHT_STATUS_CHANGED = "insight.status_changed"
    INSIGHT_EDITED = "insight.edited"
    OPPORTUNITY_CARD_GENERATED = "opportunity_card.generated"
    FACT_CREATED = "fact.created"
    FACT_STATUS_CHANGED = "fact.status_changed"
    LISTING_GENERATED = "listing.generated"
    LISTING_EDITED = "listing.edited"
    LISTING_APPROVED = "listing.approved"
    LISTING_EXPORTED = "listing.exported"


class FactType(StrEnum):
    """Product fact categories (plan section 6.6)."""

    MATERIAL = "material"
    SIZE = "size"
    WEIGHT = "weight"
    CAPACITY = "capacity"
    ACCESSORY = "accessory"
    COLOR = "color"
    USAGE_LIMITATION = "usage_limitation"
    CERTIFICATION = "certification"


class FactStatus(StrEnum):
    """Verification lifecycle of a product fact (plan section 11.2)."""

    UNVERIFIED = "unverified"
    USER_CONFIRMED = "user_confirmed"
    DOCUMENT_CONFIRMED = "document_confirmed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ListingStatus(StrEnum):
    """Listing version lifecycle (plan section 12.3)."""

    DRAFT = "draft"
    APPROVED = "approved"


class Sentiment(StrEnum):
    """Sentiment of an insight cluster (plan section 9.1)."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Severity(StrEnum):
    """How serious/urgent a pain point is."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InsightStatus(StrEnum):
    """Lifecycle of an insight (plan section 9.3)."""

    GENERATED = "generated"
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class EvidenceType(StrEnum):
    """Kinds of evidence an insight can cite (plan section 9.2)."""

    RAW_REVIEW = "raw_review"
    REVIEW_EXCERPT = "review_excerpt"
    AGGREGATED_TOPIC = "aggregated_topic"
    TREND_METRIC = "trend_metric"
    PRODUCT_ATTRIBUTE = "product_attribute"
    PRICE_OBSERVATION = "price_observation"
    SALES_RANK_OBSERVATION = "sales_rank_observation"
    USER_CONFIRMED_FACT = "user_confirmed_fact"


class OpportunityCardStatus(StrEnum):
    DRAFT = "draft"
    FINAL = "final"


class Currency(StrEnum):
    USD = "USD"


class Marketplace(StrEnum):
    AMAZON_US = "amazon_us"


class Locale(StrEnum):
    ZH_CN = "zh-CN"
    EN_US = "en-US"
