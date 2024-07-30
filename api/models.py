from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.utils.translation import gettext_lazy as _
from django_autoutils.model_utils import AbstractModel
from phonenumber_field.modelfields import PhoneNumberField

from util.field_names import S


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
    user_image = models.ImageField(_("user image"), upload_to='user_images/', null=True, blank=True)
    role = models.CharField(_("user role"), choices=UserRoleChoices.choices, default=UserRoleChoices.USER)

    objects = CustomUserManager()

    USERNAME_FIELD = S.PHONE_NUMBER
    REQUIRED_FIELDS = [S.PHONE_NUMBER, S.FIRST_NAME, S.LAST_NAME, S.ROLE]

    def __str__(self):
        return self.get_full_name()

    # def has_perm(self, perm, obj=None):
    #     return True

    # def has_module_perms(self, app_label):
    #     return True

    @property
    def is_admin(self):
        return self.role == User.UserRoleChoices.ADMIN


class Food(AbstractModel):
    name = models.CharField(_("name"), max_length=255)
    image = models.ImageField(_("image"), upload_to='food_images/', null=True, blank=True)
    description = models.TextField(_("description"), null=True, blank=True)
    rate = models.FloatField(_("rate"), default=0)

    def __str__(self):
        return self.name


class Meal(AbstractModel):
    date = models.DateField(_("date"))
    food = models.ForeignKey(Food, on_delete=models.PROTECT)
    rate = models.FloatField(_("rate"), default=0)

    def __str__(self):
        return f"{self.date} {self.food}"


class Comment(AbstractModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    text = models.TextField(_("text"))

    def __str__(self):
        return f"{self.user} {self.meal}"


class Rate(AbstractModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    meal = models.ForeignKey(Meal, on_delete=models.SET_NULL)
    rate = models.IntegerField(_("rate"), default=5)

    def __str__(self):
        return f"{self.meal} {self.rate}"
