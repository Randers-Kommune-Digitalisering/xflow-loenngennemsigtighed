"""Provide an authenticated client for upstream API requests."""

import base64
import logging
import time

logger = logging.getLogger(__name__)


class APIClient:
    """Send requests to an upstream API with optional authentication."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        auth_url: str | None = None,
        realm: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        username: str | None = None,
        password: str | None = None,
        cert_base64: str | None = None,
        use_bearer: bool | None = None,
        add_auth_to_path: bool = True,
        use_subkey: bool | None = None,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.auth_url = auth_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.use_bearer = use_bearer
        self.use_subkey = use_subkey

        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.refresh_token_expiry = None
        self.cert_data = None

        self.add_auth_to_path = add_auth_to_path

        if cert_base64:
            self.cert_data = base64.b64decode(cert_base64)

    def make_request(self, **kwargs: object) -> object:
        """Make an authenticated request and return its decoded response.

        :param **kwargs: Request options passed to the requests library. Supports
            an optional path relative to the configured base URL.
        :return: JSON data or response bytes from the upstream API.
        :raises ValueError: If the request path or headers have an invalid type.
        """
        if "path" in kwargs and kwargs["path"] is not None and not isinstance(kwargs["path"], str):
            raise ValueError("Path must be a string")

        if self.cert_data:
            import requests_pkcs12 as requests

            kwargs["pkcs12_data"] = self.cert_data
            kwargs["pkcs12_password"] = self.password
        else:
            import requests

        if "path" in kwargs:
            url = self.base_url.rstrip("/") + "/" + kwargs.pop("path").lstrip("/")
        else:
            url = self.base_url

        if "headers" in kwargs:
            if not isinstance(kwargs["headers"], dict):
                raise ValueError("Headers must be a dictionary")

            kwargs["headers"] = kwargs["headers"] | self._authenticate()
        else:
            kwargs["headers"] = self._authenticate()

        if not any(ele in kwargs for ele in ["method", "json", "data", "files"]):
            method = requests.get
        elif "method" in kwargs:
            method = getattr(requests, kwargs["method"].lower())
        else:
            method = requests.post

        kwargs.pop("method", None)

        if "json" in kwargs:
            kwargs["headers"]["Content-Type"] = "application/json"

        response = method(url, **kwargs)

        if response.status_code >= 400:
            logger.warning("Upstream API request failed (HTTP %s)", response.status_code)

        response.raise_for_status()

        if "application/json" in response.headers.get("Content-Type", ""):
            return response.json()
        else:
            if not response.content:
                return b" "

            return response.content

    def _authenticate(self) -> dict[str, str]:
        try:
            import requests

            if self.api_key:
                if self.use_bearer:
                    return {"Authorization": f"Bearer {self.api_key}"}
                elif self.use_subkey:
                    return {"Authorization": f"SubKey {self.api_key}"}
                else:
                    return {"Authorization": f"{self.api_key}"}
            elif self.client_id and self.client_secret:
                if not self.realm:
                    raise ValueError("Realm is required for client_id and client_secret authentication")

                refresh_token = False

                if self.access_token and self.token_expiry and time.time() < self.token_expiry:
                    return {"Authorization": f"Bearer {self.api_key}"}

                if (
                    self.access_token
                    and self.token_expiry
                    and time.time() >= self.token_expiry
                    and self.refresh_token
                    and self.refresh_token_expiry
                    and time.time() < self.refresh_token_expiry
                ):
                    refresh_token = True

                tmp_base_url = self.auth_url or self.base_url

                if self.add_auth_to_path:
                    tmp_url = f"{tmp_base_url}/auth/realms/{self.realm}/protocol/openid-connect/token"
                else:
                    tmp_url = f"{tmp_base_url}/realms/{self.realm}/protocol/openid-connect/token"

                tmp_headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                }

                tmp_json_data = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }

                if refresh_token:
                    tmp_json_data["grant_type"] = "refresh_token"
                    tmp_json_data["refresh_token"] = self.refresh_token

                if self.username and self.password:
                    tmp_json_data["grant_type"] = "password"
                    tmp_json_data["username"] = self.username
                    tmp_json_data["password"] = self.password
                else:
                    tmp_json_data["grant_type"] = "client_credentials"

                now = time.time()

                response = requests.post(tmp_url, headers=tmp_headers, data=tmp_json_data)

                response.raise_for_status()
                data = response.json()

                self.access_token = data["access_token"]
                self.token_expires = now + data["expires_in"]

                if "refresh_token" in data:
                    self.refresh_token = data["refresh_token"]
                    self.refresh_token_expiry = now + data["refresh_expires_in"]

                return {"Authorization": f"Bearer {self.access_token}"}
            elif self.username and self.password:
                auth_str = f"{self.username}:{self.password}"
                b64_auth_str = base64.b64encode(auth_str.encode()).decode()
                return {"Authorization": f"Basic {b64_auth_str}"}
            else:
                return {}
        except Exception as error:
            logger.error(error)
            return {}
