from typing import Iterable
from django.db import models
from decimal import Decimal
from django.db.models import Sum, Max
from datetime import datetime

# Create your model

class Company(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kompaniya nomi")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    direktor = models.CharField(max_length=150, verbose_name="Direktor")
    location = models.CharField(max_length=255, verbose_name="Manzil")
    bank = models.CharField(max_length=150, verbose_name="Bank")
    xp = models.CharField(max_length=100, verbose_name="x/p")
    mfo = models.CharField(max_length=100, verbose_name="mfo")
    inn = models.CharField(max_length=100, verbose_name="inn")
    telefon = models.CharField(max_length=255, verbose_name="Telefonlar ")

class City(models.Model):
    company = models.ForeignKey(to=Company, on_delete=models.SET_NULL, null=True, verbose_name="Kompaniya")
    name = models.CharField(max_length=100, verbose_name="Shahar nomi")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

    def __str__(self) -> str:
        return self.name


    
class Building(models.Model):
    city = models.ForeignKey(to=City, on_delete=models.SET_NULL, null=True, verbose_name="Shahar")
    name = models.CharField(max_length=150, verbose_name="Bino nomi")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")
    padez = models.IntegerField(verbose_name="Padezlar soni")
    padez_home = models.JSONField(verbose_name="Xonadonlar soni")
    floor = models.IntegerField(verbose_name="Qavatlar")
    status = models.BooleanField(verbose_name="Qo'shilgan", default=False)


    def __str__(self) -> str:
        return self.name
    

class HomeInformation(models.Model):
    padez_number = models.IntegerField(verbose_name="Padez raqami")
    home_number = models.CharField(max_length=200, verbose_name="Uy raqami")
    home_floor = models.IntegerField(verbose_name="Qavat")
    xona = models.IntegerField(verbose_name="Xonalar soni")
    field = models.FloatField(verbose_name="Uy maydoni (m/kv)")
    price = models.PositiveIntegerField(verbose_name="Uy narxi")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")
    home_model_id = models.IntegerField(verbose_name="Home model ID", null=True)
    busy = models.BooleanField(verbose_name="Band", default=False)


class Home(models.Model):
    building = models.ForeignKey(to=Building, on_delete=models.CASCADE, verbose_name="Bino")
    home = models.ForeignKey(to=HomeInformation, on_delete=models.CASCADE, verbose_name="Uy")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    
class ClientInformation(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="To'liq ism")
    phone = models.CharField(max_length=255, verbose_name="Telefon raqam")
    heard = models.CharField(max_length=200, verbose_name="Qayerda eshitgan")
    created = models.DateTimeField(auto_now_add=True)


        
class Client(models.Model):
    """Shartnoma"""
    client = models.ForeignKey(to=ClientInformation, on_delete=models.SET_NULL, null=True, verbose_name="Mijoz")
    contract = models.PositiveIntegerField(verbose_name="Shartnoma raqami", null=True, blank=True)
    home = models.ForeignKey(to=Home, on_delete=models.SET_NULL, null=True, verbose_name="Uy")
    passport = models.CharField(max_length=15, verbose_name="Passport")
    passport_muddat = models.CharField(max_length=25, verbose_name="Berilgan vaqti", null=True)
    given = models.CharField(max_length=100, verbose_name="Berilgan joyi", null=True)
    location = models.CharField(max_length=255, verbose_name="Manzili", null=True)
    term = models.IntegerField(verbose_name="To'lov muddati (oy)")
    payment = models.PositiveIntegerField(verbose_name="Oldindan to'lov")
    home_price = models.PositiveIntegerField(verbose_name="Xonadon narxi", null=True, blank=True)
    pay_date = models.PositiveIntegerField(verbose_name="To'lov qilish sanasi", null=True, blank=True)
    residual = models.DecimalField(max_digits=50, decimal_places=0, editable=False, verbose_name="Qolgan to'lov")
    oylik_tolov = models.DecimalField(max_digits=50, decimal_places=0, editable=False, verbose_name="Oylik to'lov")
    count_month = models.IntegerField(editable=False, verbose_name="Qolgan oylar")
    residu = models.IntegerField(editable=False, verbose_name="Oydan qogan to'lov")
    status = models.CharField(max_length=20, verbose_name="Holati")
    debt = models.BooleanField(default=False, verbose_name="Qarzdor")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")
    
    def save(self, *args, **kwargs):
        if not self.contract:
            max_order = Client.objects.aggregate(Max("contract"))["contract__max"]
            self.contract = (max_order or 0) + 1
        super().save(*args, **kwargs)


class Rasrochka(models.Model):
    client = models.ForeignKey(to=Client, on_delete=models.SET_NULL, null=True, verbose_name="Mijoz")
    month = models.IntegerField(verbose_name="Oy raqami")
    amount = models.IntegerField(verbose_name="To'lov miqdori")
    amount_paid = models.IntegerField(verbose_name="To'langan miqdor")
    qoldiq = models.IntegerField(verbose_name="Oy uchun qoldiq", editable=False)
    pay_date = models.DateTimeField(verbose_name="O'xirgi to'lov sanasi")
    date = models.DateTimeField(verbose_name="To'lov sanasi")

    def save(self, *args, **kwargs):
        self.qoldiq = self.amount - self.amount_paid
        self.pay_date = datetime.now()
        super().save(*args, **kwargs)
    
class ClientTrash(models.Model):
    client = models.ForeignKey(to=ClientInformation, on_delete=models.SET_NULL, null=True, verbose_name="Mijoz")
    home = models.ForeignKey(to=Home, on_delete=models.SET_NULL, null=True, verbose_name="Uy")
    passport = models.CharField(max_length=15, verbose_name="Passport")
    term = models.IntegerField(verbose_name="To'lov muddati (oy)")
    payment = models.PositiveIntegerField(verbose_name="Oldindan to'lov")
    residual = models.DecimalField(max_digits=50, decimal_places=0, editable=False, verbose_name="Qolgan to'lov")
    oylik_tolov = models.DecimalField(max_digits=50, decimal_places=0, editable=False, verbose_name="Oylik to'lov")
    count_month = models.IntegerField(editable=False, verbose_name="Qolgan oylar")
    status = models.CharField(max_length=20, verbose_name="Holati")
    debt = models.BooleanField(default=False, verbose_name="Qarzdor")
    created = models.DateTimeField(verbose_name="Yaratilgan vaqti")
    trash_created = models.DateTimeField(auto_now_add=True, verbose_name="Savatda yaratilgan")
    

