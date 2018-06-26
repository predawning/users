"""
API error exception

These will be caught and turned into an error response by our API classes.
"""

from rest_framework import status
import logging

log = logging.getLogger(__name__)


class APIError(Exception):
    """
    When an error is encountered by our API code, a subclass of this is
    thrown. Our custom `BaseAPIView` will return an error response with
    the proper JSON fields.

    You need to override this base class and its attributes.
    """
    # HTTP status response code
    status_code = None

    # Error code string
    code = None

    # True if the user is (to be) logged in
    authenticate = False

    # Fallback/debug message template
    message_template = None

    # Dict of headers to be sent in response, if any
    headers = None

    # ---- Do not implement these ----
    # Internal: Actual rendered message
    message = None

    # Optional context data dict to render an error message client-side
    context = None

    def __init__(self, *args, **kwargs):
        if self.message is not None:
            raise ValueError("self.message must be None, use message_template")
        if self.status_code is None or self.code is None:
            raise NotImplementedError(
                "One or more of the required Error fields is not defined")

        if kwargs:
            self.context = kwargs
            try:
                self.message = self.message_template.format_map(self.context)
            except KeyError as e:
                log.error("Key missing in error template context: %s %r",
                          e, self.context.keys(), exc_info=True)
                self.message = self.message_template
        else:
            self.message = self.message_template

        log.info("API error response (%s): %s",
                 self.__class__.__name__, self.data())

        super(APIError, self).__init__(self.message)

    def data(self):
        """Return data to be sent back as JSON to the client"""
        return dict(
            error_msg=self.message,
            error_authenticate=self.authenticate,
            error_code=self.code,
            error_context=self.context,
        )


class SerializerValidationError(APIError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "serializer_validation_error"
    authenticate = False
    message_template = "Serializer validation error - check err_fields"

    def __init__(self, serializer_errors, **kwargs):
        """
        :param serializer_errors: `serializer.errors` value
        :type serializer_errors: dict
        """
        self._err_fields = serializer_errors
        super(SerializerValidationError, self).__init__(**kwargs)

    def data(self):
        data = super(SerializerValidationError, self).data()
        data['err_fields'] = self._err_fields
        return data


class NotExistError(APIError):
    """Generic Not Exist error on Request."""
    status_code = status.HTTP_404_NOT_FOUND
    code = 'not_exist'
    authenticate = False
    message_template = "Not Exist: {msg}"


class PhoneRegistered(APIError):
    """Phone already registered."""
    status_code = status.HTTP_409_CONFLICT
    code = 'phone_registered'
    authenticate = False
    message_template = "This phone has been registered - try login."


class PhoneUnregistered(APIError):
    """Phone not registered."""
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'phone_unregistered'
    authenticate = False
    message_template = "Phone not found in our records"


class AccountInactive(APIError):
    """Account deprecated."""
    status_code = status.HTTP_400_BAD_REQUEST
    code = "account_inactive"
    authenticate = False
    message_template = "Your account is inactive."


class PhoneVerificationSendFailed(APIError):
    """Phone verification code could not be sent"""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = 'phone_verification_send_failed'
    authenticate = False
    message_template = "Error sending phone verification code ({msg})"


class PhoneVerificationError(APIError):
    """Phone verification code invalid

    This happens when the code is incorrect, never sent or expired.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'phone_verification_error'
    authenticate = False
    message_template = "Invalid phone verification code"


class PasswordNotExist(APIError):
    """Didn't set password while login with password"""
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'password_not_exist'
    authenticate = False
    message_template = "Didn't setup password - please setup one first."


class IncorrectPassword(APIError):
    """Password verification failed."""
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'incorrect_password'
    authenticate = False
    message_template = "Incorrect password"


class InvalidNewPassword(APIError):
    """Password verification failed."""
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'incorrect_new_password'
    authenticate = False
    message_template = "Incorrect new password"


class InvalidNewPasswordSameAsOldPassword(APIError):
    """Password verification failed."""
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'incorrect_new_password_same_as_old_password'
    authenticate = False
    message_template = "Incorrect new password same as old password"


class InvalidRiskLevel(APIError):
    """Invalid risk_level."""
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'invalid_risk_level'
    authenticate = False
    message_template = "Invalid risk level."


class InvalidDateFormat(APIError):
    """Invalid date format"""
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'invalid_date_format'
    authenticate = False
    message_template = 'Invalid date {date_str}.'


class PortfolioNoNeedRebalance(APIError):
    """Portfolio do not need rebalance"""
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'portfolio_no_need_rebalance'
    authenticate = True
    message_template = 'Your portfolio do not need rebalance.'


class PortfolioCannotModify(APIError):
    """Portfolio can not modify"""
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'portfolio_cannot_modify'
    authenticate = True
    message_template = 'Your portfolio cannot modify now.'


class PortfolioRedemptionInvalidAmount(APIError):
    """After redemption, portfolio's amount < MIN_AMOUNT """
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'portfolio_redemption_invalid_amount'
    authenticate = True
    message_template = "Your portfolio's left amount smaller then {min_amount}."


class PortfolioAppendInvalidAmount(APIError):
    """Portfolio append amount smaller than MIN_APPEND"""
    status_code = status.HTTP_400_BAD_REQUEST
    code = 'portfolio_append_invalid_amount'
    authenticate = True
    message_template = 'You cannot append smaller than {min_append}.'
