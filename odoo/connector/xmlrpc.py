import logging
import xmlrpc.client
from typing import Any

from odoo.connector.base import (
    OdooAuthenticationError,
    OdooConnection,
    OdooConnectionError,
)

logger = logging.getLogger(__name__)


class OdooXMLRPCConnection(OdooConnection):
    """
    Odoo connection implementation using XML-RPC protocol.
    This is the standard and most commonly used method for connecting to Odoo.
    """

    def __init__(
        self,
        base_url: str,
        database: str,
        username: str,
        password: str,
        timeout: int = 30,
        max_retries: int = 3,
        cache_timeout: int = 3600,
    ):
        """
        Initialize XML-RPC connection to Odoo.

        Args:
            base_url: Base URL of the Odoo instance
            database: Database name
            username: Username for authentication
            password: Password for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            cache_timeout: Cache timeout for authentication
        """
        super().__init__(
            base_url=base_url,
            database=database,
            username=username,
            password=password,
            timeout=timeout,
            max_retries=max_retries,
            cache_timeout=cache_timeout,
        )

        # XML-RPC endpoints
        self.common_endpoint = f"{self.base_url}/xmlrpc/2/common"
        self.object_endpoint = f"{self.base_url}/xmlrpc/2/object"

        # XML-RPC proxies
        self.common_proxy = None
        self.object_proxy = None

    def _create_xmlrpc_proxies(self):
        """Create XML-RPC proxy objects."""
        # Create transport with timeout
        transport = xmlrpc.client.Transport()
        transport.timeout = self.timeout

        # Create proxies
        self.common_proxy = xmlrpc.client.ServerProxy(
            self.common_endpoint,
            transport=transport,
            allow_none=True,
        )

        self.object_proxy = xmlrpc.client.ServerProxy(
            self.object_endpoint,
            transport=transport,
            allow_none=True,
        )

    def _perform_authentication(self) -> dict[str, Any] | None:
        """
        Authenticate using XML-RPC authenticate method.

        Returns:
            Dictionary with user_id and session info
        """
        try:
            if not self.common_proxy:
                self._create_xmlrpc_proxies()

            # Authenticate using XML-RPC
            user_id = self.common_proxy.authenticate(
                self.database, self.username, self.password, {}
            )

            if user_id:
                logger.info(
                    f"XML-RPC authentication successful for user {self.username}"
                )
                return {
                    "user_id": user_id,
                    "token": f"xmlrpc_{user_id}",  # Simple token for XML-RPC
                }
            logger.error(f"XML-RPC authentication failed for user {self.username}")
            return None

        except Exception as e:
            logger.error(f"XML-RPC authentication error: {e!s}")
            raise OdooAuthenticationError(f"XML-RPC authentication failed: {e!s}")

    def _perform_logout(self) -> None:
        """Logout from XML-RPC session."""
        try:
            # XML-RPC doesn't have explicit logout, just clear session
            if self.object_proxy:
                # Clear any session data if needed
                pass
        except Exception as e:
            logger.warning(f"Error during XML-RPC logout: {e!s}")

    def call_method(self, model: str, method: str, *args, **kwargs) -> Any:
        """
        Call a method on an Odoo model using XML-RPC.

        Args:
            model: Odoo model name (e.g., 'account.move', 'res.partner')
            method: Method name to call (e.g., 'create', 'read', 'write', 'search')
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Result of the method call

        Raises:
            OdooConnectionError: If the call fails
        """
        if not self.is_authenticated():
            self.authenticate()

        try:
            if not self.object_proxy:
                self._create_xmlrpc_proxies()

            # Call the method
            result = self.object_proxy.execute_kw(
                self.database, self._user_id, self.password, model, method, args, kwargs
            )

            return result

        except Exception as e:
            logger.error(f"XML-RPC method call failed: {model}.{method} - {e!s}")
            raise OdooConnectionError(f"Method call failed: {e!s}")

    def search_read(
        self,
        model: str,
        domain: list,
        fields: list | None = None,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list:
        """
        Search and read records from an Odoo model.

        Args:
            model: Odoo model name
            domain: Search domain (list of tuples)
            fields: List of fields to read
            offset: Number of records to skip
            limit: Maximum number of records to return
            order: Order by clause

        Returns:
            List of records
        """
        kwargs = {
            "domain": domain,
            "fields": fields or [],
            "offset": offset,
        }

        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order

        return self.call_method(model, "search_read", **kwargs)

    def create_record(
        self,
        model: str,
        values: dict[str, Any],
    ) -> int:
        """
        Create a new record in an Odoo model.

        Args:
            model: Odoo model name
            values: Dictionary of field values

        Returns:
            ID of the created record
        """
        return self.call_method(model, "create", values)

    def update_record(
        self,
        model: str,
        record_id: int,
        values: dict[str, Any],
    ) -> bool:
        """
        Update an existing record in an Odoo model.

        Args:
            model: Odoo model name
            record_id: ID of the record to update
            values: Dictionary of field values to update

        Returns:
            True if update was successful
        """
        return self.call_method(model, "write", [record_id], values)

    def delete_record(
        self,
        model: str,
        record_id: int,
    ) -> bool:
        """
        Delete a record from an Odoo model.

        Args:
            model: Odoo model name
            record_id: ID of the record to delete

        Returns:
            True if deletion was successful
        """
        return self.call_method(model, "unlink", [record_id])

    def read_record(
        self,
        model: str,
        record_id: int,
        fields: list | None = None,
    ) -> dict[str, Any]:
        """
        Read a single record from an Odoo model.

        Args:
            model: Odoo model name
            record_id: ID of the record to read
            fields: List of fields to read

        Returns:
            Dictionary containing the record data
        """
        return self.call_method(model, "read", [record_id], {"fields": fields or []})

    def search_records(
        self,
        model: str,
        domain: list,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list:
        """
        Search for records in an Odoo model.

        Args:
            model: Odoo model name
            domain: Search domain (list of tuples)
            offset: Number of records to skip
            limit: Maximum number of records to return
            order: Order by clause

        Returns:
            List of record IDs
        """
        kwargs = {
            "domain": domain,
            "offset": offset,
        }

        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order

        return self.call_method(model, "search", **kwargs)

    def get_model_fields(
        self,
        model: str,
    ) -> dict[str, Any]:
        """
        Get field definitions for an Odoo model.

        Args:
            model: Odoo model name

        Returns:
            Dictionary containing field definitions
        """
        return self.call_method(model, "fields_get")

    def test_connection(self) -> bool:
        """
        Test the XML-RPC connection to Odoo.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to authenticate
            if not self.authenticate():
                return False

            # Try to get version info
            if not self.common_proxy:
                self._create_xmlrpc_proxies()

            version_info = self.common_proxy.version()
            logger.info(
                f"Odoo version: {version_info.get('server_version', 'Unknown')}"
            )

            return True

        except Exception as e:
            logger.error(f"XML-RPC connection test failed: {e!s}")
            return False
