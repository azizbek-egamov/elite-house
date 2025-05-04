from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from main.models import *
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import IsAuthenticated

# Create your views here.


class Contracts(APIView):
    def get(self, request):
        contract = Client.objects.all()
        serializer = ClientSerializer(contract, many=True)
        return Response(serializer.data)


class QarzdorlarView(APIView):
    def get(self, request):
        qarzdorlar = Client.objects.filter(debt=True)
        if qarzdorlar.exists():
            serializer = ClientSerializer(qarzdorlar, many=True)
            return Response(
                {"status": True, "debtors": True, "debtors_list": serializer.data}
            )
        else:
            return Response(
                {"status": True, "debtors": False, "message": "There are no debtors"}
            )


class BuildingSaleView(APIView):
    def get(self, request):
        cities = City.objects.all()
        buildings = Building.objects.all()
        homes = Home.objects.all()

        if homes.exists() and buildings.exists():
            result = []
            for city in cities:
                city_data = {"city_name": city.name, "buildings": []}

                city_buildings = buildings.filter(city=city)
                for building in city_buildings:
                    building_data = {
                        "building_name": building.name,
                        "sold_homes": [],
                        "unsold_homes": [],
                    }

                    building_homes = Home.objects.filter(building=building)
                    for home in building_homes:

                        home_info = home.home
                        home_data = {
                            "home_number": home_info.home_number,
                            "floor": home_info.home_floor,
                            "field": home_info.field,
                            "price": home_info.price,
                            "busy": home_info.busy,
                        }

                        if home_info.busy:
                            building_data["sold_homes"].append(home_data)
                        else:
                            building_data["unsold_homes"].append(home_data)

                    city_data["buildings"].append(building_data)
                result.append(city_data)

            return Response({"status": True, "data": result})
        else:
            return Response(
                {"status": False, "message": "Buildings or homes not found."}
            )


class TushumView(APIView):
    def get(self, request):
        company_id = request.GET.get("company__id")
    
        """Kunlik, haftalik va oylik tushumlarni qaytaradi"""
        today = timezone.now().date()
        one_week_ago = today - timedelta(days=7)
        one_month_ago = today - timedelta(days=30)

        if company_id and company_id.isdigit():
            sotuv = Rasrochka.objects.filter(client__home__building__city__company__pk=company_id)
        else:
            sotuv = Rasrochka.objects.all()
            

        kunlik_tushum = 0
        haftalik_tushum = 0
        oylik_tushum = 0
        umumiy = 0

        if sotuv.exists():
            for i in sotuv:
                if i.date.date() == today:
                    kunlik_tushum += i.amount
                if i.date.date() >= one_week_ago:
                    haftalik_tushum += i.amount
                if i.date.date() >= one_month_ago:
                    oylik_tushum += i.amount
                umumiy += i.amount

            return Response(
                {
                    "status": True,
                    "kunlik_tushum": "{:,}".format(int(kunlik_tushum)).replace(",", " "),
                    "haftalik_tushum": "{:,}".format(haftalik_tushum).replace(",", " "),
                    "oylik_tushum": "{:,}".format(int(oylik_tushum)).replace(",", " "),
                    "umumiy": "{:,}".format(int(umumiy)).replace(",", " "),
                },
            )
        else:
            return Response(
                {
                    "status": True,
                    "kunlik_tushum": 0,
                    "haftalik_tushum": 0,
                    "oylik_tushum": 0,
                    "umumiy": 0,
                },
            )
