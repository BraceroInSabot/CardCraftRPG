"""Session authentication that answers ``401`` (not ``403``) to anonymous requests."""

from rest_framework import authentication


class SessionAuthentication(authentication.SessionAuthentication):
    """DRF's session auth with CSRF checks, plus a ``WWW-Authenticate`` value.

    DRF only uses ``401 Unauthorized`` when the authenticator names a scheme;
    otherwise anonymous calls get ``403``. The SPA relies on 401 to send the
    user to the login page, while 403 keeps meaning "CSRF / not allowed".
    """

    def authenticate_header(self, request) -> str:
        return 'Session realm="api"'
