from functools import wraps
import logging
from typing import Callable
from typing import Optional
from typing import cast

from flask import _request_ctx_stack
from flask import request
from flask_jwt_extended.utils import get_jwt_identity
from flask_jwt_extended.view_decorators import jwt_required
import sentry_sdk

from pcapi.core.users.models import User
from pcapi.core.users.repository import find_user_by_email
from pcapi.models.api_errors import ForbiddenError
from pcapi.routes.native.v1.blueprint import JWT_AUTH
from pcapi.serialization.spec_tree import add_security_scheme


logger = logging.getLogger(__name__)


def authenticated_user_required(route_function):  # type: ignore
    add_security_scheme(route_function, JWT_AUTH)

    @wraps(route_function)
    @jwt_required()
    def retrieve_authenticated_user(*args, **kwargs):  # type: ignore
        user = _setup_context(_user_not_none_and_active)
        return route_function(user, *args, **kwargs)

    return retrieve_authenticated_user


def authenticated_user_required_allow_inactive(route_function):  # type: ignore
    add_security_scheme(route_function, JWT_AUTH)

    @wraps(route_function)
    @jwt_required()
    def retrieve_authenticated_user(*args, **kwargs):  # type: ignore
        user = _setup_context(_user_not_none)
        return route_function(user, *args, **kwargs)

    return retrieve_authenticated_user


def _setup_context(user_checker: Callable[[Optional[User]], bool]) -> User:
    email = get_jwt_identity()
    user = find_user_by_email(email)
    if user_checker(user):
        logger.info("Authenticated user with email %s not found or inactive", email)
        raise ForbiddenError({"email": ["Utilisateur introuvable"]})

    user = cast(User, user)

    # push the user to the current context - similar to flask-login
    ctx = _request_ctx_stack.top
    ctx.user = user

    # the user is set in sentry in before_request, way before we do the
    # token auth so it needs to be also set here.
    sentry_sdk.set_user({"id": user.id})
    sentry_sdk.set_tag("device.id", request.headers.get("device-id", None))

    return user


def _user_not_none_and_active(user: User) -> bool:
    return user is None or not user.isActive


def _user_not_none(user: User) -> bool:
    return user is None
