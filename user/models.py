from django.utils.functional import cached_property

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

from utils.strings.db_names import D
from utils.strings.field_names import S


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None):
        if not phone_number:
            raise ValueError('Users must have a phone number')
        user = self.model(phone_number=phone_number)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None):
        user = self.create_user(phone_number, password)
        user.role = 'admin'
        user.save(using=self._db)
        return user


class User(AbstractUser):
    class UserRoleChoices(models.IntegerChoices):
        USER = 1, _('user')
        ADMIN = 2, _('admin')

    phone_number = PhoneNumberField(_("phone number"), db_index=True, unique=True)
    user_image = models.ImageField(_("user image"), upload_to='user_images/', blank=True,
                                   default="user_images/default avatar.jpg")
    role = models.CharField(_("user role"), max_length=6, choices=UserRoleChoices.choices,
                            default=UserRoleChoices.USER)

    objects = CustomUserManager()

    USERNAME_FIELD = S.PHONE_NUMBER
    REQUIRED_FIELDS = [S.FIRST_NAME, S.LAST_NAME, S.ROLE]

    def __str__(self):
        return self.get_full_name()

    # def has_perm(self, perm, obj=None):
    #     return True

    # def has_module_perms(self, app_label):
    #     return True

    @cached_property
    def is_admin(self):
        return self.role == User.UserRoleChoices.ADMIN

    class Meta:
        db_table = D.USER
        verbose_name = _("user")
        verbose_name_plural = _("users")
        constraints = [
            models.UniqueConstraint(fields=[S.PHONE_NUMBER], condition=models.Q(is_active=True),
                                    name=f"{S.UNIQUE}_{S.USER}1",
                                    violation_error_message=_("user with this phone number was exists"))
        ]
