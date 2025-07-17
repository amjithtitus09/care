import logging
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urljoin

import requests
from django.core.cache import cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class OdooConnectionError(Exception):
    """Base exception for Odoo connection errors"""


class OdooAuthenticationError(OdooConnectionError):
    """Exception raised when authentication fails"""


class OdooConnection(ABC):
    """
    Base class for Odoo connections that handles connection metadata and authentication.
    This class provides a foundation for connecting to Odoo instances with proper
    error handling, retry logic, and session management.
    """

    def __init__(
        self,
        base_url: str,
        database: str,
        username: str,
        password: str,
        api_key: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
        cache_timeout: int = 3600,
    ):
        """
        Initialize Odoo connection with authentication details.

        Args:
            base_url: Base URL of the Odoo instance (e.g., 'https://odoo.example.com')
            database: Database name to connect to
            username: Username for authentication
            password: Password for authentication
            api_key: Optional API key for external API access
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            cache_timeout: Cache timeout for authentication tokens in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.database = database
        self.username = username
        self.password = password
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_timeout = cache_timeout

        # Session management
        self.session = self._create_session()
        self._auth_token = None
        self._user_id = None

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic and proper headers."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
            backoff_factor=1,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        if self.api_key:
            session.headers.update(
                {
                    "X-API-Key": self.api_key,
                }
            )

        return session

    def _get_cache_key(self, key: str) -> str:
        """Generate cache key for this connection."""
        return f"odoo_connection_{self.database}_{self.username}_{key}"

    def authenticate(self) -> bool:
        """
        Authenticate with Odoo and store session information.

        Returns:
            True if authentication successful, False otherwise
        """
        # cache_key = self._get_cache_key("auth_token")

        # # Check cache first
        # cached_auth = cache.get(cache_key)
        # if cached_auth:
        #     self._auth_token = cached_auth.get("token")
        #     self._user_id = cached_auth.get("user_id")
        #     return True

        try:
            # Attempt authentication
            auth_data = self._perform_authentication()

            if auth_data:
                self._auth_token = auth_data.get("token")
                self._user_id = auth_data.get("user_id")

                # Cache authentication data
                # cache.set(
                #     cache_key,
                #     {
                #         "token": self._auth_token,
                #         "user_id": self._user_id,
                #     },
                #     self.cache_timeout,
                # )

                logger.info(
                    f"Successfully authenticated with Odoo for user {self.username}"
                )
                return True
            logger.error(f"Authentication failed for user {self.username}")
            return False

        except Exception as e:
            logger.error(f"Authentication error for user {self.username}: {e!s}")
            raise OdooAuthenticationError(f"Failed to authenticate: {e!s}")

    @abstractmethod
    def _perform_authentication(self) -> dict[str, Any] | None:
        """
        Perform the actual authentication with Odoo.
        This method should be implemented by subclasses to handle
        different authentication methods (XML-RPC, REST API, etc.).

        Returns:
            Dictionary containing authentication data (token, user_id, etc.)
            or None if authentication failed
        """

    def is_authenticated(self) -> bool:
        """Check if the connection is currently authenticated."""
        return self._auth_token is not None and self._user_id is not None

    def logout(self) -> None:
        """Logout and clear authentication data."""
        try:
            if self.is_authenticated():
                self._perform_logout()
        except Exception as e:
            logger.warning(f"Error during logout: {e!s}")
        finally:
            self._auth_token = None
            self._user_id = None
            cache.delete(self._get_cache_key("auth_token"))

    @abstractmethod
    def _perform_logout(self) -> None:
        """Perform the actual logout operation."""

    def get_auth_headers(self) -> dict[str, str]:
        """Get headers required for authenticated requests."""
        if not self.is_authenticated():
            raise OdooConnectionError("Not authenticated. Call authenticate() first.")

        headers = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        return headers

    def make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        """
        Make an authenticated request to Odoo.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to base_url)
            data: Request data for POST/PUT requests
            params: Query parameters
            headers: Additional headers

        Returns:
            requests.Response object

        Raises:
            OdooConnectionError: If request fails
        """
        if not self.is_authenticated():
            self.authenticate()

        url = urljoin(self.base_url, endpoint)
        request_headers = self.get_auth_headers()

        if headers:
            request_headers.update(headers)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=self.timeout,
            )

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {url} - {e!s}")
            raise OdooConnectionError(f"Request failed: {e!s}")

    def test_connection(self) -> bool:
        """
        Test the connection to Odoo.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to authenticate
            if not self.authenticate():
                return False

            # Make a simple API call to verify connection
            response = self.make_request("GET", "/api/version")
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Connection test failed: {e!s}")
            return False

    def __enter__(self):
        """Context manager entry."""
        self.authenticate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logout()

    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.logout()
        except:
            pass
