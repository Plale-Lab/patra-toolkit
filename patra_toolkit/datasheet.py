import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from . import client
from .exceptions import PatraSubmissionError
from .patra_model_card import ModelCardJSONEncoder


@dataclass
class DatasheetPublisher:
    name: str
    publisher_identifier: Optional[str] = None
    publisher_identifier_scheme: Optional[str] = None
    scheme_uri: Optional[str] = None
    lang: Optional[str] = None


@dataclass
class DatasheetCreator:
    creator_name: str
    name_type: Optional[str] = None
    lang: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    name_identifier: Optional[str] = None
    name_identifier_scheme: Optional[str] = None
    name_id_scheme_uri: Optional[str] = None
    affiliation: Optional[str] = None
    affiliation_identifier: Optional[str] = None
    affiliation_identifier_scheme: Optional[str] = None
    affiliation_scheme_uri: Optional[str] = None


@dataclass
class DatasheetTitle:
    title: str
    title_type: Optional[str] = None
    lang: Optional[str] = None


@dataclass
class DatasheetSubject:
    subject: str
    subject_scheme: Optional[str] = None
    scheme_uri: Optional[str] = None
    value_uri: Optional[str] = None
    classification_code: Optional[str] = None
    lang: Optional[str] = None


@dataclass
class DatasheetContributor:
    contributor_type: str
    contributor_name: str
    name_type: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    name_identifier: Optional[str] = None
    name_identifier_scheme: Optional[str] = None
    name_id_scheme_uri: Optional[str] = None
    affiliation: Optional[str] = None
    affiliation_identifier: Optional[str] = None
    affiliation_identifier_scheme: Optional[str] = None
    affiliation_scheme_uri: Optional[str] = None


@dataclass
class DatasheetDate:
    date: str
    date_type: str
    date_information: Optional[str] = None


@dataclass
class DatasheetAlternateIdentifier:
    alternate_identifier: str
    alternate_identifier_type: str


@dataclass
class DatasheetRelatedIdentifier:
    related_identifier: str
    related_identifier_type: str
    relation_type: str
    related_metadata_scheme: Optional[str] = None
    scheme_uri: Optional[str] = None
    scheme_type: Optional[str] = None
    resource_type_general: Optional[str] = None


@dataclass
class DatasheetRights:
    rights: Optional[str] = None
    rights_uri: Optional[str] = None
    rights_identifier: Optional[str] = None
    rights_identifier_scheme: Optional[str] = None
    scheme_uri: Optional[str] = None
    lang: Optional[str] = None


@dataclass
class DatasheetDescription:
    description: str
    description_type: str
    lang: Optional[str] = None


@dataclass
class DatasheetGeoLocation:
    geo_location_place: Optional[str] = None
    point_longitude: Optional[float] = None
    point_latitude: Optional[float] = None
    box_west: Optional[float] = None
    box_east: Optional[float] = None
    box_south: Optional[float] = None
    box_north: Optional[float] = None
    polygon: Optional[dict] = None


@dataclass
class DatasheetFundingReference:
    funder_name: str
    funder_identifier: Optional[str] = None
    funder_identifier_type: Optional[str] = None
    scheme_uri: Optional[str] = None
    award_number: Optional[str] = None
    award_uri: Optional[str] = None
    award_title: Optional[str] = None


@dataclass
class Datasheet:
    """
    Represents a DataCite-style datasheet describing a dataset. Build one field-by-field
    (or via the add_*()/set_publisher() convenience methods) and submit() it to the Patra
    server, as an alternative to filling in the same fields through the Patra UI.

    Example:
        .. code-block:: python

            ds = Datasheet(publication_year=2025, version="1.0")
            ds.add_title("My Dataset")
            ds.add_creator("Jane Doe")
            ds.submit(patra_server_url="http://localhost:8000", token="access_token")
    """
    uuid: Optional[str] = None
    publication_year: Optional[int] = None
    resource_type: Optional[str] = None
    resource_type_general: Optional[str] = None
    size: Optional[str] = None
    format: Optional[str] = None
    version: Optional[str] = None
    is_private: bool = False
    publisher: Optional[DatasheetPublisher] = None
    creators: List[DatasheetCreator] = field(default_factory=list)
    titles: List[DatasheetTitle] = field(default_factory=list)
    subjects: List[DatasheetSubject] = field(default_factory=list)
    contributors: List[DatasheetContributor] = field(default_factory=list)
    dates: List[DatasheetDate] = field(default_factory=list)
    alternate_identifiers: List[DatasheetAlternateIdentifier] = field(default_factory=list)
    related_identifiers: List[DatasheetRelatedIdentifier] = field(default_factory=list)
    rights_list: List[DatasheetRights] = field(default_factory=list)
    descriptions: List[DatasheetDescription] = field(default_factory=list)
    geo_locations: List[DatasheetGeoLocation] = field(default_factory=list)
    funding_references: List[DatasheetFundingReference] = field(default_factory=list)

    def add_creator(self, creator_name: str, **kwargs) -> DatasheetCreator:
        creator = DatasheetCreator(creator_name=creator_name, **kwargs)
        self.creators.append(creator)
        return creator

    def add_title(self, title: str, title_type: Optional[str] = None,
                  lang: Optional[str] = None) -> DatasheetTitle:
        t = DatasheetTitle(title=title, title_type=title_type, lang=lang)
        self.titles.append(t)
        return t

    def add_subject(self, subject: str, **kwargs) -> DatasheetSubject:
        s = DatasheetSubject(subject=subject, **kwargs)
        self.subjects.append(s)
        return s

    def add_description(self, description: str, description_type: str,
                         lang: Optional[str] = None) -> DatasheetDescription:
        d = DatasheetDescription(description=description, description_type=description_type, lang=lang)
        self.descriptions.append(d)
        return d

    def add_date(self, date: str, date_type: str,
                 date_information: Optional[str] = None) -> DatasheetDate:
        d = DatasheetDate(date=date, date_type=date_type, date_information=date_information)
        self.dates.append(d)
        return d

    def add_funding_reference(self, funder_name: str, **kwargs) -> DatasheetFundingReference:
        f = DatasheetFundingReference(funder_name=funder_name, **kwargs)
        self.funding_references.append(f)
        return f

    def set_publisher(self, name: str, **kwargs) -> DatasheetPublisher:
        self.publisher = DatasheetPublisher(name=name, **kwargs)
        return self.publisher

    def __str__(self) -> str:
        """
        Returns:
            str: A JSON-formatted string representation of the datasheet.
        """
        return json.dumps(self.__dict__, cls=ModelCardJSONEncoder, indent=4, separators=(',', ': '))

    def validate(self) -> bool:
        """
        Lightweight validation: requires at least one non-empty title and one non-empty
        creator, matching what the Patra server's own duplicate-detection logic keys off.
        The server itself does not require any fields, so this is a usability check rather
        than a schema validation.

        Returns:
            bool: True if the datasheet has at least one title and one creator.
        """
        ok = True
        if not self.titles or not any(t.title.strip() for t in self.titles):
            logging.error("Datasheet validation error: at least one non-empty title is required.")
            ok = False
        if not self.creators or not any(c.creator_name.strip() for c in self.creators):
            logging.error("Datasheet validation error: at least one non-empty creator is required.")
            ok = False
        return ok

    def save(self, file_location: str) -> None:
        """
        Saves the datasheet as a JSON file to the specified location.

        Args:
            file_location (str): Path where the datasheet JSON file will be saved.
        """
        try:
            with open(file_location, 'w', encoding='utf-8') as json_file:
                json_file.write(str(self))
            logging.info("Datasheet created.")
        except IOError as io_err:
            logging.error(f"Failed to save datasheet: {io_err}")

    def submit(self, patra_server_url: str, token: Optional[str] = None) -> dict:
        """
        Submits the datasheet to the Patra server.

        Args:
            patra_server_url (str): The URL of the Patra server.
            token (Optional[str]): The X-Tapis-Token access token for authentication.

        Returns:
            dict: The server's ingest result (asset_type, asset_id, asset_uuid, organization,
            created, duplicate).

        Raises:
            PatraSubmissionError: If validation fails, the server is unreachable, or the
                server returns an error other than a duplicate.
            PatraDatasheetExistsError: If an equivalent datasheet already exists on the server.
        """
        if not self.validate():
            raise PatraSubmissionError("Datasheet validation failed; see log for details.")

        payload = json.loads(str(self))
        result = client.submit_datasheet(patra_server_url, payload, token=token)
        self.uuid = result.get("asset_uuid")
        return result

    @classmethod
    def list_datasheets(cls, server_url: str, token: Optional[str] = None, q: Optional[str] = None,
                         skip: int = 0, limit: int = 50) -> List[dict]:
        """
        Lists datasheets on the Patra server.

        Args:
            server_url (str): The URL of the Patra server.
            token (Optional[str]): The X-Tapis-Token access token (includes private records if provided).
            q (Optional[str]): Optional substring search.
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return (server max: 100).

        Returns:
            List[dict]: Summaries shaped like {identifier, uuid, title, creator, category,
            is_private, updated_at}.
        """
        return client.list_datasheets(server_url, token=token, q=q, skip=skip, limit=limit)

    @classmethod
    def get_datasheet(cls, server_url: str, uuid: str, token: Optional[str] = None) -> dict:
        """
        Retrieves a single datasheet by uuid from the Patra server.

        Args:
            server_url (str): The URL of the Patra server.
            uuid (str): The datasheet's uuid.
            token (Optional[str]): The X-Tapis-Token access token (required for private datasheets).

        Returns:
            dict: The full DataCite-style datasheet detail.
        """
        return client.get_datasheet(server_url, uuid, token=token)
