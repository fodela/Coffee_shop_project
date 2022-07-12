import json
import os
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from dotenv import load_dotenv

# look for a file named .env and load my database username and password
load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
ALGORITHMS = os.getenv("AUTH0_ALGO")
API_AUDIENCE = os.getenv("API_AUDIENCE")

# AuthError Exception
"""
AuthError Exception
A standardized way to communicate auth failure modes
"""


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header


def get_token_auth_header():
    # check if request is an authorization request
    if "Authorization" not in request.headers:
        raise AuthError(
            {
                "code": "missing_authorization_header",
                "description": "Authorization header must be provided"
            }, 401
        )

    # get the request
    auth_header = request.headers["Authorization"]
    header_parts = auth_header.split(" ")
    # validation
    # check if both header and token exist in the authorization request
    if len(header_parts) != 2:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "authorization header must contain both bearer and token"
            }, 401
        )

    # Check if it is a bearer request
    elif header_parts[0].lower() != "bearer":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must contain 'bearer'"
            }, 401
        )

    return header_parts[1]


def check_permissions(permission, payload):
    # Payload must have permissions. | AuthError400
    if "permissions" not in payload:
        raise AuthError(
            {
                "code": "missing_permissions",
                "description": "payload does not have permission"
            }, 400
        )

    # permission must match permission in the payload. | authError403
    if permission not in payload["permissions"]:
        raise AuthError(
            {
                "code": "invalid_permissions",
                "description": "permission does not match permission in payload"
            }, 403
        )

    return True


"""
    !!NOTE urlopen has a common certificate error described here:
    https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
"""


def verify_decode_jwt(token):
    # GET THE PUBLIC KEY FROM AUTH0
    jsonurl = urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")

    jwks = json.loads(jsonurl.read())

    # GET THE DATA IN THE HEADER
    unverified_header = jwt.get_unverified_header(token)

    # CHOOSE OUR KEY
    rsa_key = {}

    if "kid" not in unverified_header:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization malformed.",
            },
            401,
        )
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }

    # Finally, verify!!!
    if rsa_key:
        try:
            # Use the key to validate the jwt
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/",
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError(
                {
                    "code": "token_expired",
                    "description": "Token expired",
                },
                401,
            )
        except jwt.JWTClaimsError:
            raise AuthError(
                {
                    "code": "invalid_claims",
                    "description": "Incorrect claims. Please, check the audience and issuer",
                },
                401,
            )
        except Exception:
            raise AuthError(
                {
                    "code": "invalid_header",
                    "description": "Unable to parse authentication token.",
                },
                400,
            )
    raise AuthError(
        {
            "code": "invalid_header",
            "description": "Unable to find the appropriate key",
        },
        400,
    )


def requires_auth(permission=""):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator
