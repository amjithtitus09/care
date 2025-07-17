"""
Odoo Connector Module

This module provides connection implementations for integrating with Odoo.
The JSON-RPC connector is the recommended approach for modern Odoo instances.
"""

from .base import OdooAuthenticationError, OdooConnection, OdooConnectionError
from .jsonrpc import OdooJSONRPCConnection

# Default connection class (JSON-RPC)
OdooConnection = OdooJSONRPCConnection

__all__ = [
    "OdooAuthenticationError",
    "OdooConnection",
    "OdooConnectionError",
    "OdooJSONRPCConnection",
]
