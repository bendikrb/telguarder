"""telguarder models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.types import Discriminator


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)


class LookupType(str, Enum):
    COMPANY = "company"
    PERSON = "person"


class SpamType(str, Enum):
    COMMUNITY = "community"


@dataclass
class BaseDataClassORJSONMixin(DataClassORJSONMixin):
    class Config(BaseConfig):
        omit_none = True
        allow_deserialization_not_by_alias = True


@dataclass
class LookupRequest(BaseDataClassORJSONMixin):
    numbers: list[str]
    text: str | None = None
    offset: int | None = None
    count: int | None = None
    min_score: int | None = field(default=None, metadata=field_options(alias="minScore"))


@dataclass
class SpamInfo(BaseDataClassORJSONMixin):
    spam_type: SpamType = field(metadata=field_options(alias="spamType"))
    message: str
    title: str
    info_page_url: str = field(metadata=field_options(alias="infoPageUrl"))


@dataclass
class PhoneNumber(BaseDataClassORJSONMixin):
    primary: str
    secondary: str | None = None


@dataclass
class Address(BaseDataClassORJSONMixin):
    street: str
    place: str
    zip: str
    country: str


@dataclass
class Coordinates(BaseDataClassORJSONMixin):
    longitude: float
    latitude: float
    address: Address | None = None


@dataclass
class LookupResultEntity(BaseDataClassORJSONMixin):
    id: str
    type: LookupType
    phone_numbers: PhoneNumber | None = field(default=None, metadata=field_options(alias="phoneNumbers"))
    mobile_numbers: PhoneNumber | None = field(default=None, metadata=field_options(alias="mobileNumbers"))
    address: Address | None = None
    coordinates: Coordinates | None = None
    spam: SpamInfo | None = None
    origin: str | None = None

    class Config(BaseConfig):
        discriminator = Discriminator(
            field="type",
            include_subtypes=True,
        )


@dataclass(kw_only=True)
class LookupResultCompany(LookupResultEntity):
    type = LookupType.COMPANY
    name: str
    organization_numbers: list[str] = field(metadata=field_options(alias="organizationNumbers"))
    visiting_address: Address | None = field(default=None, metadata=field_options(alias="visitingAddress"))
    log_web_url: str | None = field(default=None, metadata=field_options(alias="logWebUrl"))
    logo_url: str | None = field(default=None, metadata=field_options(alias="logoUrl"))
    web_url: str | None = field(default=None, metadata=field_options(alias="webUrl"))
    web_url_text: str | None = field(default=None, metadata=field_options(alias="webUrlText"))


@dataclass(kw_only=True)
class LookupResultPerson(LookupResultEntity):
    type = LookupType.PERSON
    first_name: str = field(metadata=field_options(alias="firstName"))
    middle_name: str | None = field(default=None, metadata=field_options(alias="middleName"))
    last_name: str = field(metadata=field_options(alias="lastName"))
    birth_date: datetime | None = field(
        default=None,
        metadata=field_options(
            alias="birthDate",
            deserialize=lambda v: datetime.fromisoformat(v) if v else None,
            serialize=lambda v: datetime.isoformat(v) if v else None,
        ),
    )


@dataclass
class LookupResult(BaseDataClassORJSONMixin):
    number: str
    search_id: str = field(metadata=field_options(alias="searchId"))
    result: list[LookupResultEntity]
    error: bool
    security_level: int = field(metadata=field_options(alias="securityLevel"))
    is_valid: bool = field(metadata=field_options(alias="isValid"))
    info_page_url: str = field(metadata=field_options(alias="infoPageUrl"))
    reported_by_users: int = field(metadata=field_options(alias="reportedByUsers"))
    number_verified: bool = field(metadata=field_options(alias="numberVerified"))
    spam: SpamInfo | None = None


@dataclass
class LookupResults(BaseDataClassORJSONMixin):
    results: list[LookupResult]
    request: LookupRequest
    query_time: int = field(default=None, metadata=field_options(alias="queryTime"))
    execute_time: int = field(default=None, metadata=field_options(alias="executeTime"))
