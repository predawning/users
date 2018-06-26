from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class UserManager(UserManager):
    def create_by_phone(self, phone, **kwargs):
        return self.create_user(phone, phone=phone, **kwargs)


class User(AbstractUser):
    """
    User - AUTH_USER_MODEL
    """

    # phone - used for register & login
    phone = models.CharField(_('phone'), max_length=30, unique=True,
                             null=True, blank=True,
                             help_text=_('Mobile phone number'))
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('last update'), auto_now=True)
    verified = models.BooleanField(
        _('verified'), default=False,
        help_text=_('User has verified phone using a text message'))
    verified_ts = models.DateTimeField(_('verification timestamp'),
                                       null=True, blank=True)
    objects = UserManager()

    def mark_verified(self):
        self.verified = True
        self.verified_ts = timezone.now()
        self.save()

    def set_password(self, raw_password):
        if raw_password:
            super(User, self).set_password(raw_password)

    def check_password(self, raw_password):
        if self.password:
            return super(User, self).check_password(raw_password)
        return True

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
