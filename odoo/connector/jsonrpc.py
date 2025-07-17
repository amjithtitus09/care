import logging
from typing import Any

import requests

from odoo.connector.base import (
    OdooAuthenticationError,
    OdooConnection,
    OdooConnectionError,
)

logger = logging.getLogger(__name__)


class OdooJSONRPCConnection(OdooConnection):
    """
    Odoo connection implementation using JSON-RPC protocol.
    This is the modern and preferred method for connecting to Odoo.
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
        Initialize JSON-RPC connection to Odoo.

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

        # JSON-RPC endpoints
        self.json_endpoint = f"{self.base_url}/web/dataset/call_kw"
        self.session_endpoint = f"{self.base_url}/web/session/authenticate"
        self.logout_endpoint = f"{self.base_url}/web/session/destroy"

        # Session management
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # Configure retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
            backoff_factor=1,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _perform_authentication(self) -> dict[str, Any] | None:
        """
        Authenticate using JSON-RPC session authentication.

        Returns:
            Dictionary with user_id and session info
        """
        try:
            # Prepare authentication payload
            auth_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": self.database,
                    "login": self.username,
                    "password": self.password,
                },
                "id": 1,
            }

            # Make authentication request
            response = self.session.post(
                self.session_endpoint,
                json=auth_data,
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()

            # Check for authentication errors
            if "error" in result:
                error_msg = (
                    result["error"]
                    .get("data", {})
                    .get("message", "Authentication failed")
                )
                logger.error(f"JSON-RPC authentication error: {error_msg}")
                raise OdooAuthenticationError(f"Authentication failed: {error_msg}")

            # Check if authentication was successful
            if result.get("result") and result["result"].get("uid"):
                user_id = result["result"]["uid"]
                logger.info(
                    f"JSON-RPC authentication successful for user {self.username}"
                )
                return {
                    "user_id": user_id,
                    "token": f"jsonrpc_{user_id}",
                }

            logger.error(f"JSON-RPC authentication failed for user {self.username}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"JSON-RPC authentication request error: {e!s}")
            raise OdooAuthenticationError(f"Authentication request failed: {e!s}")
        except Exception as e:
            logger.error(f"JSON-RPC authentication error: {e!s}")
            raise OdooAuthenticationError(f"Authentication failed: {e!s}")

    def _perform_logout(self) -> None:
        """Logout from JSON-RPC session."""
        try:
            logout_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {},
                "id": 1,
            }

            self.session.post(
                self.logout_endpoint,
                json=logout_data,
                timeout=self.timeout,
            )
        except Exception as e:
            logger.warning(f"Error during JSON-RPC logout: {e!s}")

    def _make_jsonrpc_request(self, method: str, params: dict[str, Any]) -> Any:
        """
        Make a JSON-RPC request to Odoo.

        Args:
            method: Method to call
            params: Parameters for the method

        Returns:
            Response data

        Raises:
            OdooConnectionError: If the request fails
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": params,
                "id": 1,
            }

            response = self.session.post(
                self.json_endpoint,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()

            # Check for errors
            if "error" in result:
                error_msg = (
                    result["error"].get("data", {}).get("message", "Request failed")
                )
                logger.error(f"JSON-RPC request error: {error_msg}")
                raise OdooConnectionError(f"Request failed: {error_msg}")

            return result.get("result")

        except requests.exceptions.RequestException as e:
            logger.error(f"JSON-RPC request error: {e!s}")
            raise OdooConnectionError(f"Request failed: {e!s}")
        except Exception as e:
            logger.error(f"JSON-RPC request error: {e!s}")
            raise OdooConnectionError(f"Request failed: {e!s}")

    def call_method(self, model: str, method: str, *args, **kwargs) -> Any:
        """
        Call a method on an Odoo model using JSON-RPC.

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

        # Prepare parameters for the method call
        params = {
            "model": model,
            "method": method,
            "args": list(args),
            "kwargs": kwargs,
        }

        return self._make_jsonrpc_request("call", params)

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
        Test the JSON-RPC connection to Odoo.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to authenticate
            if not self.authenticate():
                return False

            # Try to get version info using a simple method call
            version_info = self.call_method("ir.module.module", "search_count", [])
            logger.info("JSON-RPC connection test successful")
            return True

        except Exception as e:
            logger.error(f"JSON-RPC connection test failed: {e!s}")
            return False

    def get_version_info(self) -> dict[str, Any]:
        """
        Get Odoo version information.

        Returns:
            Dictionary containing version information
        """
        try:
            # Use the common endpoint to get version info
            version_endpoint = f"{self.base_url}/web/webclient/version_info"
            response = self.session.get(version_endpoint, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Could not get version info: {e!s}")
            return {}
