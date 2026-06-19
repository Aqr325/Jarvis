"""
Public API schemas - for external data services.
"""

from typing import Optional, List
from pydantic import Field, field_validator
from ..schemas.base import BaseSchema, ResponseBase


class CryptoRequest(BaseSchema):
    """Cryptocurrency price request."""
    
    coin_id: str = Field(default="bitcoin", max_length=128, description="Coin identifier")
    vs_currency: str = Field(default="usd", max_length=64, description="Currency to compare")
    
    @field_validator('vs_currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        # Common currencies, validation extends at API level
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "coin_id": "bitcoin",
                "vs_currency": "usd",
            }
        }


class ExchangeRequest(BaseSchema):
    """Currency exchange rate request."""
    
    from_currency: str = Field(..., min_length=3, max_length=3, pattern=r'^[A-Z]{3}$', description="Source currency code")
    to_currency: str = Field(..., min_length=3, max_length=3, pattern=r'^[A-Z]{3}$', description="Target currency code")
    amount: float = Field(default=1.0, ge=0, description="Amount to convert")
    
    @field_validator('from_currency', 'to_currency')
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_currency": "USD",
                "to_currency": "CNY",
                "amount": 100.0,
            }
        }


class DictionaryRequest(BaseSchema):
    """Dictionary lookup request."""
    
    word: str = Field(..., min_length=1, max_length=128, description="Word to look up")
    language: str = Field(default="en", max_length=10, description="Dictionary language")
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "word": "serendipity",
                "language": "en",
            }
        }


class HolidayRequest(BaseSchema):
    """Public holidays request."""
    
    year: int = Field(default=2026, ge=2000, le=2100, description="Year to query")
    country_code: str = Field(default="CN", min_length=2, max_length=3, description="ISO country code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "year": 2026,
                "country_code": "CN",
            }
        }


class JokeRequest(BaseSchema):
    """Joke request."""
    
    category: str = Field(default="Any", max_length=64, description="Joke category")
    lang: str = Field(default="en", max_length=10, description="Language code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "Any",
                "lang": "en",
            }
        }


class BookSearchRequest(BaseSchema):
    """Book search request."""
    
    query: str = Field(..., min_length=1, max_length=256, description="Search query")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Python programming",
                "limit": 10,
            }
        }


class BookISBNRequest(BaseSchema):
    """ISBN lookup request."""
    
    isbn: str = Field(..., min_length=10, max_length=20, description="ISBN-10 or ISBN-13")
    
    @field_validator('isbn')
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        # Remove hyphens for validation
        clean = v.replace('-', '').replace(' ', '')
        if not clean.isdigit() and not (len(clean) == 10 and clean[:-1].isdigit() and clean[-1].upper() == 'X'):
            raise ValueError('invalid ISBN format')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "isbn": "978-0-596-51774-8",
            }
        }
