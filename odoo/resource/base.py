import logging
from abc import ABC
from typing import Any

from django.conf import settings

from odoo.connector.base import OdooConnection, OdooConnectionError
from odoo.connector.jsonrpc import OdooJSONRPCConnection

logger = logging.getLogger(__name__)


class OdooResourceError(Exception):
    """Base exception for Odoo resource operations"""


class OdooResourceNotFoundError(OdooResourceError):
    """Exception raised when a resource is not found"""


class OdooResourceValidationError(OdooResourceError):
    """Exception raised when resource data validation fails"""


class OdooResource(ABC):
    """
    Base class for Odoo resources that handles business logic for specific Odoo models.
    This class provides a foundation for creating, reading, updating, and deleting
    records in Odoo with proper validation and error handling.
    """

    # Odoo model name (e.g., 'account.move', 'res.partner')
    MODEL_NAME: str = None

    # Fields that should be included in create operations
    CREATE_FIELDS: list[str] = []

    # Fields that should be included in update operations
    UPDATE_FIELDS: list[str] = []

    # Fields that should be included in read operations
    READ_FIELDS: list[str] = []

    # Default search domain for this resource
    DEFAULT_DOMAIN: list = []

    # Default ordering for search results
    DEFAULT_ORDER: str = "id desc"

    def __init__(self, connection: OdooConnection = None):
        """
        Initialize the resource with an Odoo connection.

        Args:
            connection: Odoo connection instance
        """
        if not connection:
            connection = self.get_default_connection()

        self.connection = connection
        self._validate_connection()

    def _validate_connection(self) -> None:
        """Validate that the connection is properly configured."""
        if not isinstance(self.connection, OdooConnection):
            raise ValueError("connection must be an instance of OdooConnection")

    def _validate_data(
        self, data: dict[str, Any], operation: str = "create"
    ) -> dict[str, Any]:
        """
        Validate data before sending to Odoo.

        Args:
            data: Data to validate
            operation: Operation type ('create', 'update', 'read')

        Returns:
            Validated and cleaned data

        Raises:
            OdooResourceValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise OdooResourceValidationError("Data must be a dictionary")

        # Get allowed fields for this operation
        allowed_fields = getattr(self, f"{operation.upper()}_FIELDS", [])

        if allowed_fields:
            # Filter data to only include allowed fields
            filtered_data = {k: v for k, v in data.items() if k in allowed_fields}

            # Check for required fields
            missing_fields = [field for field in allowed_fields if field not in data]
            if missing_fields:
                raise OdooResourceValidationError(
                    f"Missing required fields for {operation}: {missing_fields}"
                )

            return filtered_data

        return data

    def _prepare_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare data for create operation.

        Args:
            data: Raw data

        Returns:
            Prepared data for create operation
        """
        return self._validate_data(data, "create")

    def _prepare_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare data for update operation.

        Args:
            data: Raw data

        Returns:
            Prepared data for update operation
        """
        return self._validate_data(data, "update")

    def _prepare_read_fields(self, fields: list[str] | None = None) -> list[str]:
        """
        Prepare fields for read operation.

        Args:
            fields: List of fields to read

        Returns:
            List of fields to read
        """
        if fields is None:
            return self.READ_FIELDS or []

        # Validate that all requested fields are allowed
        allowed_fields = set(self.READ_FIELDS or [])
        if allowed_fields:
            invalid_fields = [f for f in fields if f not in allowed_fields]
            if invalid_fields:
                raise OdooResourceValidationError(
                    f"Invalid fields for read operation: {invalid_fields}"
                )

        return fields

    def create(self, data: dict[str, Any]) -> int:
        """
        Create a new record in Odoo.

        Args:
            data: Data for the new record

        Returns:
            ID of the created record

        Raises:
            OdooResourceError: If creation fails
            OdooResourceValidationError: If data validation fails
        """
        try:
            prepared_data = self._prepare_create_data(data)
            record_id = self.connection.create_record(self.MODEL_NAME, prepared_data)

            logger.info(f"Created {self.MODEL_NAME} record with ID: {record_id}")
            return record_id

        except OdooConnectionError as e:
            logger.error(f"Failed to create {self.MODEL_NAME} record: {e!s}")
            raise OdooResourceError(f"Failed to create record: {e!s}")
        except OdooResourceValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating {self.MODEL_NAME} record: {e!s}")
            raise OdooResourceError(f"Unexpected error: {e!s}")

    def update(self, record_id: int, data: dict[str, Any]) -> bool:
        """
        Update an existing record in Odoo.

        Args:
            record_id: ID of the record to update
            data: Data to update

        Returns:
            True if update was successful

        Raises:
            OdooResourceError: If update fails
            OdooResourceValidationError: If data validation fails
        """
        try:
            prepared_data = self._prepare_update_data(data)
            success = self.connection.update_record(
                self.MODEL_NAME, record_id, prepared_data
            )

            if success:
                logger.info(f"Updated {self.MODEL_NAME} record with ID: {record_id}")
            else:
                logger.warning(
                    f"Update operation returned False for {self.MODEL_NAME} record ID: {record_id}"
                )

            return success

        except OdooConnectionError as e:
            logger.error(
                f"Failed to update {self.MODEL_NAME} record {record_id}: {e!s}"
            )
            raise OdooResourceError(f"Failed to update record: {e!s}")
        except OdooResourceValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error updating {self.MODEL_NAME} record {record_id}: {e!s}"
            )
            raise OdooResourceError(f"Unexpected error: {e!s}")

    def delete(self, record_id: int) -> bool:
        """
        Delete a record from Odoo.

        Args:
            record_id: ID of the record to delete

        Returns:
            True if deletion was successful

        Raises:
            OdooResourceError: If deletion fails
        """
        try:
            success = self.connection.delete_record(self.MODEL_NAME, record_id)

            if success:
                logger.info(f"Deleted {self.MODEL_NAME} record with ID: {record_id}")
            else:
                logger.warning(
                    f"Delete operation returned False for {self.MODEL_NAME} record ID: {record_id}"
                )

            return success

        except OdooConnectionError as e:
            logger.error(
                f"Failed to delete {self.MODEL_NAME} record {record_id}: {e!s}"
            )
            raise OdooResourceError(f"Failed to delete record: {e!s}")
        except Exception as e:
            logger.error(
                f"Unexpected error deleting {self.MODEL_NAME} record {record_id}: {e!s}"
            )
            raise OdooResourceError(f"Unexpected error: {e!s}")

    def read(self, record_id: int, fields: list[str] | None = None) -> dict[str, Any]:
        """
        Read a single record from Odoo.

        Args:
            record_id: ID of the record to read
            fields: List of fields to read (optional)

        Returns:
            Dictionary containing the record data

        Raises:
            OdooResourceError: If read fails
            OdooResourceNotFoundError: If record not found
        """
        try:
            read_fields = self._prepare_read_fields(fields)
            record_data = self.connection.read_record(
                self.MODEL_NAME, record_id, read_fields
            )

            if not record_data:
                raise OdooResourceNotFoundError(
                    f"Record {record_id} not found in {self.MODEL_NAME}"
                )

            logger.debug(f"Read {self.MODEL_NAME} record with ID: {record_id}")
            return record_data

        except OdooConnectionError as e:
            logger.error(f"Failed to read {self.MODEL_NAME} record {record_id}: {e!s}")
            raise OdooResourceError(f"Failed to read record: {e!s}")
        except OdooResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error reading {self.MODEL_NAME} record {record_id}: {e!s}"
            )
            raise OdooResourceError(f"Unexpected error: {e!s}")

    def search(
        self,
        domain: list | None = None,
        fields: list[str] | None = None,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for records in Odoo.

        Args:
            domain: Search domain (optional, uses DEFAULT_DOMAIN if not provided)
            fields: List of fields to read (optional)
            offset: Number of records to skip
            limit: Maximum number of records to return
            order: Order by clause (optional, uses DEFAULT_ORDER if not provided)

        Returns:
            List of records matching the search criteria

        Raises:
            OdooResourceError: If search fails
        """
        try:
            # Use default domain if none provided
            search_domain = domain or self.DEFAULT_DOMAIN
            search_order = order or self.DEFAULT_ORDER
            read_fields = self._prepare_read_fields(fields)

            records = self.connection.search_read(
                self.MODEL_NAME,
                search_domain,
                read_fields,
                offset,
                limit,
                search_order,
            )

            logger.debug(f"Found {len(records)} {self.MODEL_NAME} records")
            return records

        except OdooConnectionError as e:
            logger.error(f"Failed to search {self.MODEL_NAME} records: {e!s}")
            raise OdooResourceError(f"Failed to search records: {e!s}")
        except Exception as e:
            logger.error(f"Unexpected error searching {self.MODEL_NAME} records: {e!s}")
            raise OdooResourceError(f"Unexpected error: {e!s}")

    def search_ids(
        self,
        domain: list | None = None,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[int]:
        """
        Search for record IDs in Odoo.

        Args:
            domain: Search domain (optional, uses DEFAULT_DOMAIN if not provided)
            offset: Number of records to skip
            limit: Maximum number of records to return
            order: Order by clause (optional, uses DEFAULT_ORDER if not provided)

        Returns:
            List of record IDs matching the search criteria

        Raises:
            OdooResourceError: If search fails
        """
        try:
            # Use default domain if none provided
            search_domain = domain or self.DEFAULT_DOMAIN
            search_order = order or self.DEFAULT_ORDER

            record_ids = self.connection.search_records(
                self.MODEL_NAME,
                search_domain,
                offset,
                limit,
                search_order,
            )

            logger.debug(f"Found {len(record_ids)} {self.MODEL_NAME} record IDs")
            return record_ids

        except OdooConnectionError as e:
            logger.error(f"Failed to search {self.MODEL_NAME} record IDs: {e!s}")
            raise OdooResourceError(f"Failed to search record IDs: {e!s}")
        except Exception as e:
            logger.error(
                f"Unexpected error searching {self.MODEL_NAME} record IDs: {e!s}"
            )
            raise OdooResourceError(f"Unexpected error: {e!s}")

    def get_fields(self) -> dict[str, Any]:
        """
        Get field definitions for this resource's model.

        Returns:
            Dictionary containing field definitions

        Raises:
            OdooResourceError: If operation fails
        """
        try:
            fields = self.connection.get_model_fields(self.MODEL_NAME)
            return fields

        except OdooConnectionError as e:
            logger.error(f"Failed to get fields for {self.MODEL_NAME}: {e!s}")
            raise OdooResourceError(f"Failed to get fields: {e!s}")
        except Exception as e:
            logger.error(
                f"Unexpected error getting fields for {self.MODEL_NAME}: {e!s}"
            )
            raise OdooResourceError(f"Unexpected error: {e!s}")

    def exists(self, record_id: int) -> bool:
        """
        Check if a record exists in Odoo.

        Args:
            record_id: ID of the record to check

        Returns:
            True if record exists, False otherwise
        """
        try:
            self.read(record_id, fields=["id"])
            return True
        except OdooResourceNotFoundError:
            return False
        except Exception:
            return False

    def count(self, domain: list | None = None) -> int:
        """
        Count records matching a domain.

        Args:
            domain: Search domain (optional, uses DEFAULT_DOMAIN if not provided)

        Returns:
            Number of records matching the domain
        """
        try:
            search_domain = domain or self.DEFAULT_DOMAIN
            record_ids = self.connection.search_records(self.MODEL_NAME, search_domain)
            return len(record_ids)
        except Exception as e:
            logger.error(f"Failed to count {self.MODEL_NAME} records: {e!s}")
            return 0

    def get_default_connection(self) -> OdooConnection:
        odoo_config = getattr(settings, "ODOO_CONFIG", {})
        return OdooJSONRPCConnection(
            base_url=odoo_config.get("base_url"),
            database=odoo_config.get("database"),
            username=odoo_config.get("username"),
            password=odoo_config.get("password"),
            timeout=odoo_config.get("timeout", 30),
            max_retries=odoo_config.get("max_retries", 3),
            cache_timeout=odoo_config.get("cache_timeout", 3600),
        )
