from django.conf import settings
from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser

from utils.strings.db_names import D
from utils.strings.field_names import S


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, full_name=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Users must have a phone number")
        user = self.model(
            phone_number=phone_number, full_name=full_name, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, phone_number, full_name=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(
            phone_number, full_name=full_name, password=password, **extra_fields
        )


class User(AbstractBaseUser):
    ROLE_CHOICES = (
        ("user", "User"),
        ("admin", "Admin"),
    )

    phone_number = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(_("full name"), max_length=150, blank=True)
    user_image = models.ImageField(
        _("user image"),
        upload_to="user_images/",
        blank=True,
    )
    role = models.CharField(
        _("user role"),
        max_length=6,
        choices=ROLE_CHOICES,
        default="user",
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = S.PHONE_NUMBER
    REQUIRED_FIELDS = [S.FULL_NAME]

    def __str__(self):
        return self.full_name

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    class Meta:
        db_table = D.USER
        verbose_name = _("user")
        verbose_name_plural = _("users")
        constraints = [
            models.UniqueConstraint(
                fields=[S.PHONE_NUMBER],
                condition=models.Q(is_active=True),
                name=f"{S.UNIQUE}_{S.USER}1",
                violation_error_message=_("user with this phone number was exists"),
            )
        ]

    def get_fcm_tokens(self):
        """Returns all FCM tokens associated with this user."""
        return self.fcm_tokens.all()
