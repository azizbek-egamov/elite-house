from django.core.management.base import BaseCommand
import time
from main.models import Client
from main.views import send_sms
import asyncio
from datetime import datetime, timedelta


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        while True:
            clients = Client.objects.all()
            for client in clients:
                if client.debt == True:
                    create = client.created
                    date = create - timedelta(days=3)
                    if client.created.date().strftime("%d-%m") == datetime.now().date().strftime("%d-%m"):
                        asyncio.run(
                            send_sms(
                                phone=client.client.phone,
                                sms=f"Assalomu alaykum {client.client.full_name}. Bugun #00{client.pk} raqamli shartnoma bo'yicha to'lov sanasi ekanligini ma'lum qilamiz. Qarzdorlik miqdori {client.residual} so'm va bu oyda to'lanadigan summa {client.oylik_tolov} so'm. To'lovni amalga oshirishni unutmang.",
                            )
                        )
                    if date.date().strftime("%d-%m") == datetime.now().date().strftime("%d-%m"):
                        asyncio.run(
                            send_sms(
                                phone=client.client.phone,
                                sms=f"Assalomu alaykum {client.client.full_name}. Sizda #00{client.pk} raqamli shartnoma bo'yicha {client.residual} so'm qarzdorlik mavjud va bu oyda to'lanadigan summa {client.oylik_tolov} so'm. To'lovni {client.created.date().strftime("%d.%m.%Y")} gacha qilishni unutmang.",
                            )
                        )
            time.sleep(86400)
