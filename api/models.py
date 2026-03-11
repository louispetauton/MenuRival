from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RestaurantCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    phone: Optional[str] = None
    website_url: Optional[str] = None
    cuisine_type: Optional[List[str]] = []
    google_stars: Optional[float] = None
    yelp_stars: Optional[float] = None
    is_subject: Optional[bool] = False
    market_id: Optional[str] = None  # defaults to SF market if not provided


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    phone: Optional[str] = None
    website_url: Optional[str] = None
    cuisine_type: Optional[List[str]] = None
    google_stars: Optional[float] = None
    yelp_stars: Optional[float] = None
    is_subject: Optional[bool] = None
    intake_status: Optional[str] = None


class RestaurantResponse(BaseModel):
    id: str
    name: str
    slug: Optional[str]
    address: Optional[str]
    neighborhood: Optional[str]
    phone: Optional[str]
    website_url: Optional[str]
    cuisine_type: Optional[List[str]]
    google_stars: Optional[float]
    yelp_stars: Optional[float]
    is_subject: bool
    intake_status: str
    market_id: Optional[str]
    created_at: datetime
    item_count: Optional[int] = 0


class URLLookupRequest(BaseModel):
    url: str


class URLLookupResponse(BaseModel):
    name: Optional[str]
    address: Optional[str]
    neighborhood: Optional[str]
    phone: Optional[str]
    website_url: Optional[str]
    cuisine_type: Optional[List[str]]
    google_stars: Optional[float]
    yelp_stars: Optional[float]


class MenuUploadResponse(BaseModel):
    pull_id: str
    restaurant_id: str
    menu_type: str
    item_count: int
    parse_status: str
    categories: List[str]


class StandardizeResponse(BaseModel):
    total_processed: int
    total_updated: int
    duration_seconds: float
    message: str


class InsightResponse(BaseModel):
    id: str
    headline: Optional[str]
    pricing_position: Optional[str]
    opportunities: Optional[list]
    gaps: Optional[list]
    date_generated: datetime


class IngestURLRequest(BaseModel):
    restaurant_id: str
    url: str
    menu_type: str = "unknown"


class GenerateInsightRequest(BaseModel):
    subject_restaurant_id: str
