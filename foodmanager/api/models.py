from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django_jalali.db import models as jmodels

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class MyUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None):
        if not phone_number:
            raise ValueError('Users must have a phone number')
        user = self.model(phone_number=phone_number)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None):
        user = self.create_user(phone_number, password)
        user.is_admin = True
        user.role = 'admin'
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )

    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, unique=True)
    user_image = models.ImageField(upload_to='user_images/', null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

class Food(models.Model):
    name = models.CharField(max_length=255)
    picture = models.ImageField(upload_to='food_pictures/',null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class Meal(models.Model):
    date = jmodels.jDateField()
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)    

    def __str__(self):
        return f"{self.date} - {self.food.name}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    text = models.TextField()
    

    def __str__(self):
        return f"{self.user.phone_number} - {self.meal.date}"
