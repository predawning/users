from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, CreateAPIView
from rest_framework.generics import RetrieveAPIView

from .errors import APIError, SerializerValidationError

class BaseAPIView(GenericAPIView):
    """
    Base class for individual API views

    We extend the GenericAPIView to handle our custom error response
    exceptions
    """

    def handle_exception(self, exc):
        """
        Adds special handling four our APIError exception

        These exceptions allow us to return a detailed error response
        from anywhere in the code, instead of having to pass the detailed
        error through various layers of calls.

        :param exc: APIError or other exception
        """
        if isinstance(exc, ValidationError):
            exc = SerializerValidationError(exc.detail)

        if isinstance(exc, APIError):
            response = Response(exc.data(), status=exc.status_code)
            if exc.headers:
                for key, val in exc.headers.items():
                    response[key] = val
            return response

        return super(BaseAPIView, self).handle_exception(exc)


class UnauthenticatedAPIView(BaseAPIView):
    """
    Base class for calls that are not expected to be authenticated
    """
    permission_classes = []
    authentication_classes = ()


class AuthenticatedAPIView(BaseAPIView):
    """
    Base class for calls that are authenticated
    Will use the DEFAULT_AUTHENTICATION_CLASSES & DEFAULT_PERMISSION_CLASSES
    """
    pass


class RetrieveCreateAPIView(RetrieveAPIView, CreateAPIView):
    pass