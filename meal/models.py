from django.db import models
from django.utils.translation import gettext_lazy as _
from django_autoutils.model_utils import AbstractModel

from user.models import User
from utils.strings.db_names import D


class Food(AbstractModel):
    name = models.CharField(_("name"), max_length=255)
    image = models.ImageField(_("image"), upload_to='food_images/', null=True, blank=True)
    description = models.TextField(_("description"), null=True, blank=True)
    rate = models.FloatField(_("rate"), default=0)

    def __str__(self):
        return self.name

    class Meta:
        db_table = D.FOOD
        verbose_name = _("food")
        verbose_name_plural = _("foods")


class Meal(AbstractModel):
    date = models.DateField(_("date"))
    food = models.ForeignKey(Food, on_delete=models.PROTECT)
    avg_rate = models.FloatField(_("rate"), default=0)

    def __str__(self):
        return f"{self.date} {self.food}"

    class Meta:
        db_table = D.MEAL
        verbose_name = _("meal")
        verbose_name_plural = _("meals")


class Comment(AbstractModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    text = models.TextField(_("text"))

    def __str__(self):
        return f"{self.user} {self.meal}"

    class Meta:
        db_table = D.COMMENT
        verbose_name = _("comment")
        verbose_name_plural = _("comments")


class Rate(AbstractModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    meal = models.ForeignKey(Meal, on_delete=models.SET_NULL, null=True)
    rate = models.IntegerField(_("rate"), default=5)

    def __str__(self):
        return f"{self.meal} {self.rate}"

    class Meta:
        db_table = D.RATE
        verbose_name = _("rate")
        verbose_name_plural = _("rates")
