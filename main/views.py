from django.shortcuts import render, redirect, HttpResponse, HttpResponseRedirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from main.models import *
from django.contrib import messages
import json
import re
import math
import unittest
import asyncio
import aiohttp
import openpyxl
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.utils.timezone import now
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from io import BytesIO
from xhtml2pdf import pisa
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from core.settings import domain
from django.urls import get_resolver
from django.template.loader import render_to_string

# Create your views here.

def UrlActive(request):
    """Get active URL path"""
    url = request.path
    resolver = get_resolver()
    # Function is incomplete - should return something
    return url


def CompanyPage(request):
    if request.user.is_authenticated and request.user.username not in {
        "financeadmin",
    }:
        company = Company.objects.order_by("-created").all()
        return render(
            request=request,
            template_name="company/company.html",
            context={"company": company},
        )

    return redirect("login")


def CompanyCreate(request):
    if request.user.is_authenticated and request.user.username not in {
        "financeadmin",
        "receptionadmin",
    }:
        if request.method == "POST":
            data = request.POST
            Company.objects.create(
                name=data.get("company"),
                location=data.get("location"),
                bank=data.get("bank"),
                xp=data.get("xp"),
                mfo=data.get("mfo"),
                inn=data.get("inn"),
                telefon=data.get("telefon"),
                direktor=data.get("dr"),
            )
            return redirect("company")

        return render(request=request, template_name="company/create.html")

    return redirect("login")


def CompanyEdit(request, id):
    if request.user.is_authenticated and request.user.username not in {
        "financeadmin",
        "receptionadmin",
    }:
        company = get_object_or_404(Company, pk=id)

        if request.method == "POST":
            name = request.POST.get("company")
            location = request.POST.get("location")
            bank = request.POST.get("bank")
            xp = request.POST.get("xp")
            mfo = request.POST.get("mfo")
            inn = request.POST.get("inn")
            telefon = request.POST.get("telefon")
            dr = request.POST.get("dr")
            if name:
                company.name = name
                company.location = location
                company.bank = bank
                company.xp = xp
                company.mfo = mfo
                company.inn = inn
                company.telefon = telefon
                company.direktor = dr
                company.save()
                messages.success(request, "Kompaniya muvaffaqiyatli tahrirlandi.")
                return redirect("company")
            else:
                messages.error(request, "Kompaniya nomi kiritilmadi.")

        return render(
            request=request,
            template_name="company/edit.html",
            context={"company": company, "error": False},
        )

    return redirect("login")


def CompanyDelete(request, id):
    if request.user.is_authenticated and request.user.username not in {
        "financeadmin",
        "receptionadmin",
    }:
        company = get_object_or_404(Company, pk=id)
        company.delete()
        messages.success(request, "Kompaniya muvaffaqiyatli o'chirildi.")
        return JsonResponse({"ok": True})

    return redirect("login")


from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import datetime, timedelta
import json

def tushum_view(request):
    company_id = request.GET.get("company__id")

    # Kunlik, haftalik va oylik tushumlarni qaytaradi
    today = timezone.now().date()
    one_week_ago = today - timedelta(days=7)
    one_month_ago = today - timedelta(days=30)

    # Company ID bo'yicha filter qilish
    if company_id and company_id.isdigit():
        sotuv = Rasrochka.objects.filter(
            client__home__building__city__company__pk=company_id
        )
    else:
        sotuv = Rasrochka.objects.all()

    # Tushumlarni hisoblash
    kunlik_tushum = 0
    haftalik_tushum = 0
    oylik_tushum = 0
    umumiy = 0

    if sotuv.exists():
        for i in sotuv:
            # Kunlik tushum
            if i.date.date() == today:
                kunlik_tushum += i.amount

            # Haftalik tushum
            if i.date.date() >= one_week_ago:
                haftalik_tushum += i.amount

            # Oylik tushum
            if i.date.date() >= one_month_ago:
                oylik_tushum += i.amount

            # Umumiy tushum
            umumiy += i.amount

        return {
            "status": True,
            "kunlik_tushum": "{:,}".format(int(kunlik_tushum)).replace(",", " "),
            "haftalik_tushum": "{:,}".format(haftalik_tushum).replace(",", " "),
            "oylik_tushum": "{:,}".format(int(oylik_tushum)).replace(",", " "),
            "umumiy": "{:,}".format(int(umumiy)).replace(",", " "),
        }
    else:
        # Agar sotuv ma'lumotlari bo'lmasa
        return {
            "status": False,
            "kunlik_tushum": "0",
            "haftalik_tushum": "0",
            "oylik_tushum": "0",
            "umumiy": "0",
        }


def HomePage(request):
    if request.user.is_authenticated:
        company_id = request.GET.get("company__id")
        launch_date = datetime(2024, 10, 1)  # Example: October 1, 2024

        # Filter buildings and clients by company_id if provided
        if company_id:
            buildings = Building.objects.filter(city__company__id=company_id)
            clients = ClientInformation.objects.all()
            contracts = Client.objects.filter(
                home__building__city__company__id=company_id
            )
            homes = Home.objects.filter(building__city__company__id=company_id)
        else:
            buildings = Building.objects.all()
            clients = ClientInformation.objects.all()
            contracts = Client.objects.all()
            homes = Home.objects.all()

        tushumlar = tushum_view(request)

        client_count = clients.count()
        one_month_ago = datetime.now().date() - timedelta(days=30)
        month_client = clients.filter(created__date__gte=one_month_ago).count()

        # Weekly client data
        week_days_uz = ["D", "S", "Ch", "P", "J", "Sh", "Y"]
        week_list = []
        week_client = []

        for i in range(7):
            day = datetime.now().date() - timedelta(days=i)
            day_name = week_days_uz[day.weekday()]
            week_list.append(day_name)
            day_client = clients.filter(created__date=day).count()
            week_client.append(day_client)

        week_list = [day.capitalize() for day in week_list]
        
        # Convert to JSON for ECharts
        week_list_json = json.dumps(week_list)
        week_client_json = json.dumps(week_client)

        # Building occupancy data
        bino_name = []
        home_ch = []
        bino_city = []
        
        for building in buildings:
            bino_name.append(building.name)
            city_name = building.city.name if building.city else "Ma'lumot yo'q"
            bino_city.append(city_name)
            
            bino_home = homes.filter(building__pk=building.pk)
            band_uylar = sum(1 for home in bino_home if home.home.busy)
            jami_uylar = bino_home.count()
            
            try:
                home_ch.append("%.2f" % float((band_uylar / jami_uylar) * 100))
            except ZeroDivisionError:
                home_ch.append("0")
        
        # Convert to JSON for ECharts
        bino_name_json = json.dumps(bino_name)
        home_ch_json = json.dumps(home_ch)
        bino_city_json = json.dumps(bino_city)

        # Client source data
        kuzatuv = []
        x, t, ins, o, yo = 0, 0, 0, 0, 0
        
        for i in clients:
            if i.heard == "Instagramda":
                ins += 1
            elif i.heard == "Telegramda":
                t += 1
            elif i.heard == "Odamlar orasida":
                o += 1
            elif i.heard == "YouTubeda":
                yo += 1
            else:
                x += 1
                
        kuzatuv.extend([ins, t, yo, o, x])
        kuzatuv_json = json.dumps(kuzatuv)

        # Monthly statistics
        month_name = [
            "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
            "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
        ]

        hozirgi_oy = datetime.now().replace(day=1)
        oylar = []

        oy = launch_date
        while oy <= hozirgi_oy:
            oylar.append(oy)
            oy = (oy + timedelta(days=32)).replace(day=1)

        if len(oylar) > 12:
            oylar = oylar[-12:]

        oylik_statistika = []

        for oy_boshi in oylar:
            oy_oxiri = (oy_boshi + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            mijozlar = clients.filter(created__date__range=(oy_boshi, oy_oxiri))
            mijoz_uy_olgan = 0
            mijoz_uy_olmagan = 0

            for mijoz in mijozlar:
                client_contracts = contracts.filter(
                    client=mijoz, created__range=(oy_boshi, oy_oxiri)
                )
                if client_contracts.exists():
                    if any(
                        contract.status in ["Rasmiylashtirilgan", "Tugallangan"]
                        for contract in client_contracts
                    ):
                        mijoz_uy_olgan += 1
                    else:
                        mijoz_uy_olmagan += 1
                else:
                    mijoz_uy_olmagan += 1

            oy_nomi = month_name[oy_boshi.month - 1]
            hozirgi_oy_statistikasi = {
                "oy": f"{oy_nomi}",
                "mijozlar_soni": len(mijozlar),
                "uy_olganlar": mijoz_uy_olgan,
                "uy_olmaganlar": mijoz_uy_olmagan,
            }

            oylik_statistika.append(hozirgi_oy_statistikasi)

        oy_mijoz = []
        oy_name = []
        uy_olgan = []
        uy_olmagan = []
        
        for oy in oylik_statistika:
            oy_name.append(oy["oy"])
            oy_mijoz.append(oy["mijozlar_soni"])
            uy_olgan.append(oy["uy_olganlar"])
            uy_olmagan.append(oy["uy_olmaganlar"])
        
        # Convert to JSON for ECharts
        month_list_json = json.dumps(oy_name)
        oy_mijoz_json = json.dumps(oy_mijoz)
        uy_olgan_json = json.dumps(uy_olgan)
        uy_olmagan_json = json.dumps(uy_olmagan)

        # Payment alert
        pay_date = 13 <= datetime.today().date().day <= 15
        pay_month = "15 - " + month_name[datetime.today().month - 1]
        
        # FIX: Determine contract status based on Rasrochka model
        contracts_completed = 0
        contracts_in_progress = 0
        
        # Get all active contracts (not canceled)
        active_contracts = contracts.exclude(status="Bekor qilingan")
        
        for contract in active_contracts:
            # Check if all payments are completed for this contract
            rasrochka_entries = Rasrochka.objects.filter(client=contract)
            total_remaining = rasrochka_entries.aggregate(Sum('qoldiq'))['qoldiq__sum'] or 0
            
            if total_remaining == 0:
                contracts_completed += 1
            else:
                contracts_in_progress += 1
        
        # Debt information - also based on Rasrochka model
        qarz = 0
        debtor_count = 0
        nodebtor_count = 0
        
        for contract in active_contracts:
            rasrochka_entries = Rasrochka.objects.filter(client=contract)
            total_remaining = rasrochka_entries.aggregate(Sum('qoldiq'))['qoldiq__sum'] or 0
            
            if total_remaining > 0:
                qarz += total_remaining
                debtor_count += 1
            else:
                nodebtor_count += 1

        # Company filter
        filter_companies = [{"url": "?", "name": "Barchasi"}]
        for comp in Company.objects.all():
            filter_companies.append({"url": f"?company__id={comp.pk}", "name": f"{comp.name}"})

        return render(
            request=request,
            template_name="index.html",
            context={
                "tushum": tushumlar,
                "client_count": client_count,
                "building_count": buildings.count(),
                "month_client": month_client,
                "contract": contracts_in_progress,  # Based on Rasrochka payments
                "contract_f": contracts_completed,  # Based on Rasrochka payments
                "qarz": "{:,}".format(int(qarz)).replace(",", " "),
                "home": homes.count(),
                "company_filter": filter_companies,
                "bino_stat": {
                    "bino_name": bino_name_json,
                    "home_ch": home_ch_json,
                    "bino_city": bino_city_json,
                },
                "kuzatuv": kuzatuv_json,
                "week_client": week_client_json,
                "week_list": week_list_json,
                "month_list": month_list_json,
                "oy_mijoz": oy_mijoz_json,
                "uy_olgan": uy_olgan_json,
                "uy_olmagan": uy_olmagan_json,
                "pay": {"date": pay_date, "month": pay_month},
                "debtors": {
                    "debtor": debtor_count,
                    "nodebtor": nodebtor_count,
                },
            },
        )

    return redirect("login")

## City


def CityPage(request):
    if request.user.is_authenticated and request.user.username != "financeadmin":
        company_id = request.GET.get("company")
        if company_id:
            cities = (
                City.objects.order_by("-created").filter(company__id=company_id).all()
            )
        else:
            cities = City.objects.order_by("-created").all()
        return render(
            request=request,
            template_name="city/city.html",
            context={"city": cities, "company_filter": Company.objects.all()},
        )

    return redirect("login")


def CityCreate(request):
    if request.user.is_authenticated and request.user.username not in {
        "financeadmin",
        "receptionadmin",
    }:
        if request.method == "POST":
            company = request.POST.get("company")
            city_name = request.POST.get("city")
            if city_name:
                City.objects.create(company_id=company, name=city_name)
                messages.success(request, "Shahar muvaffaqiyatli yaratildi.")
                return redirect("city")
            else:
                messages.error(request, "Shahar nomi kiritilmadi.")

        company = Company.objects.all()
        return render(
            request=request,
            template_name="city/create.html",
            context={"company": company},
        )

    return redirect("login")


def CityEdit(request, id):
    if request.user.is_authenticated and request.user.username not in {
        "financeadmin",
        "receptionadmin",
    }:
        city = get_object_or_404(City, pk=id)

        if request.method == "POST":
            name = request.POST.get("city")
            company = request.POST.get("company")
            if name:
                city.company_id = company
                city.name = name
                city.save()
                messages.success(request, "Shahar muvaffaqiyatli tahrirlandi.")
                return redirect("city")
            else:
                messages.error(request, "Shahar nomi kiritilmadi.")

        return render(
            request=request,
            template_name="city/edit.html",
            context={"city": city, "company": Company.objects.all(), "error": False},
        )

    return redirect("login")


def CityDelete(request, id):
    if request.user.is_authenticated and request.user.username not in {
        "financeadmin",
        "receptionadmin",
    }:
        city = get_object_or_404(City, pk=id)
        city.delete()
        messages.success(request, "Shahar muvaffaqiyatli o'chirildi.")
        return JsonResponse({"ok": True})

    return redirect("login")


## Building


def BuildingPage(request):
    if request.user.is_authenticated and request.user.username != "financeadmin":
        city_id = request.GET.get("city")
        company_id = request.GET.get("company")
        filters = {}
        if company_id and company_id.isdigit():
            filters["city__company__id"] = company_id
        if city_id and city_id.isdigit():
            filters["city__id"] = city_id

        if filters:
            buildings = Building.objects.filter(**filters)
        else:
            buildings = Building.objects.all()

        company = Company.objects.all()

        return render(
            request=request,
            template_name="building/building.html",
            context={
                "building": buildings,
                "city_filter": City.objects.all(),
                "company": Company.objects.all(),
            },
        )

    return redirect("login")


def BuildingCreate(request):
    if request.user.is_authenticated and request.user.username not in {
        "financeadmin",
        "receptionadmin",
    }:
        if request.method == "POST":
            home_count = request.POST.getlist("home_count")
            name = request.POST.get("building")
            padez_count = request.POST.get("padez_count")
            city_pk = request.POST.get("city_sel")
            floor = request.POST.get("floor")

            if not city_pk:
                Building.objects.create(
                    name=name, padez=padez_count, padez_home=home_count, floor=floor
                )
            else:
                city = City.objects.filter(pk=city_pk).first()
                if city:
                    Building.objects.create(
                        name=name,
                        padez=padez_count,
                        padez_home=home_count,
                        floor=floor,
                        city=city,
                    )
            messages.success(request, "Bino muvaffaqiyatli yaratildi.")
            return redirect("building")

        cities = City.objects.all()
        company = Company.objects.all()
        city_list = []
        for c in cities:
            city_list.append({"id": c.pk, "company": c.company.pk, "name": c.name})
        return render(
            request=request,
            template_name="building/create.html",
            context={
                "status": cities.exists(),
                "city": cities,
                "company": company,
                "city_list": city_list,
            },
        )

    return redirect("login")


def BuildingEdit(request, id):
    if request.user.is_authenticated and request.user.username not in {
        "financeadmin",
        "receptionadmin",
    }:
        building = get_object_or_404(Building, pk=id)

        if request.method == "POST":
            home_count = request.POST.getlist("home_count")
            name = request.POST.get("building")
            padez_count = request.POST.get("padez_count")
            city_pk = request.POST.get("city_sel")
            floor = request.POST.get("floor")

            if city_pk:
                city = City.objects.filter(pk=city_pk).first()
                building.city = city
            else:
                building.city = None

            building.name = name
            building.padez_home = home_count
            building.padez = padez_count
            building.floor = floor
            building.save()

            messages.success(request, "Bino muvaffaqiyatli tahrirlandi.")
            return redirect("building")

        cities = City.objects.all()
        return render(
            request=request,
            template_name="building/edit.html",
            context={"error": False, "building": building, "cityy": cities},
        )

    return redirect("login")


def BuildingDelete(request, id):
    if request.user.is_authenticated and request.user.username not in [
        "financeadmin",
        "receptionadmin",
    ]:
        building = get_object_or_404(Building, pk=id)
        building.delete()
        return JsonResponse({"ok": True})
    return redirect("login")


## Home


def HomePagee(request):
    if request.user.is_authenticated and request.user.username != "financeadmin":
        building_id = request.GET.get("building")
        city_id = request.GET.get("city")
        company_id = request.GET.get("company")
        filters = {}
        if company_id and company_id.isdigit():
            filters["building__city__company__id"] = company_id
        if city_id and city_id.isdigit():
            filters["building__city__id"] = city_id
        if building_id and building_id.isdigit():
            filters["building__id"] = building_id

        if filters:
            homes = Home.objects.filter(**filters)
        else:
            homes = Home.objects.all()

        company = Company.objects.all()
        ls = ""
        s = 1
        for param, value in request.GET.items():
            if s == 1:
                ls += f"?{param}={value}"
            else:
                ls += f"&{param}={value}"
            s += 1

        return render(
            request=request,
            template_name="home/home.html",
            context={
                "home": homes,
                "company": Company.objects.all(),
                "city": City.objects.all(),
                "building": Building.objects.all(),
                "params": ls
            },
        )

    return redirect("login")


def HomeDownload(request):
    filters = {}
    building_id = request.GET.get("building")
    city_id = request.GET.get("city")
    company_id = request.GET.get("company")
    if company_id and company_id.isdigit():
        filters["building__city__company__id"] = company_id
    if city_id and city_id.isdigit():
        filters["building__city__id"] = city_id
    if building_id and building_id.isdigit():
        filters["building__id"] = building_id
    
    if filters:
        home = Home.objects.filter(**filters)
    else:
        home = Home.objects.all()

    html_content = """
    <html>
        <head>
            <style>
            .title{
                font-size: 22px;
               text-align: center;
               border-bottom: 1px solid black;
                      font-family: "Times New Roman", Times, serif;
            }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                
                th, td {
                    border: 1px solid black;
                    padding: 6px;
                    text-align: center;
                    font-size: 17px;
                    font-family: "Times New Roman", Times, serif;
                }
                td {
                    font-weight: 200;
                }
                th {
                    background-color: #f2f2f2;
                }
                .n{
                    width: 20%
                }
                 .m{
                    width: 40%
                }
                 .i{
                    width: 40%
                }
            </style>
        </head>
        <body>
            <h2 class="title">"""

    html_content += f"""XONADONLAR MA'LUMOTLARI
    <table>
                <thead>
                    <tr>
                        <th class="n">N</th>
                        <th class="m">PODEZD</th>
                        <th class="i">QAVAT</th>
                        <th class="i">XONA</th>
                        <th class="i">M<sup>2</sup></th>
                    </tr>
                </thead>
                <tbody>
    """

    for row in home:
        html_content += f"""
                    <tr>
                        <td>{row.home.home_number}</td>
                        <td>{row.home.padez_number}</td>
                        <td>{row.home.home_floor}</td>
                        <td>{row.home.xona}</td>
                        <td>{row.home.field}</td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </body>
    </html>
    """

    # PDFni yaratish
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="XONADONLAR MA\'LUMOTLARI.pdf"'

    pisa_status = pisa.CreatePDF(BytesIO(html_content.encode("utf-8")), dest=response)
    if pisa_status.err:
        return HttpResponse("PDF yaratishda xatolik yuz berdi", status=500)

    return response


def HomeCreate(request):
    if request.user.is_authenticated and request.user.username not in [
        "financeadmin",
        "receptionadmin",
    ]:
        if request.method == "POST":
            home_areas = request.POST.getlist("home_maydon")
            building_pk = request.POST.get("building_sel")
            price = request.POST.get("mkv_price")
            home_prices = [int(price) * int(area) for area in home_areas]

            building = get_object_or_404(Building, pk=building_pk)

            padez_counts = building.padez_home
            home_number = 1
            for padez_number, apartment_count in enumerate(padez_counts, start=1):
                for apartment_number in range(1, int(apartment_count) + 1):
                    home_mkv = request.POST.get(
                        f"home_maydon_{padez_number}_{home_number}"
                    )
                    home_mkvp = request.POST.get(
                        f"home_mkv_{padez_number}_{home_number}"
                    )
                    home_floor = request.POST.get(
                        f"home_floor_{padez_number}_{home_number}"
                    )
                    home_num = request.POST.get(
                        f"home_num_{padez_number}_{home_number}"
                    )
                    home_xona = request.POST.get(
                        f"home_xona_{padez_number}_{home_number}"
                    )
                    hinfo = HomeInformation.objects.create(
                        padez_number=padez_number,
                        home_number=home_num,
                        field=home_mkv,
                        price=home_mkvp,
                        busy=0,
                        home_floor=home_floor,
                        xona=home_xona,
                    )
                    home = Home.objects.create(building=building, home=hinfo)
                    hinfo.home_model_id = home.pk
                    hinfo.save()
                    home_number += 1
            building.status = True
            building.save()

            return redirect("homee")

        js = []
        buildings = Building.objects.all()

        cities = []
        for ci in City.objects.all():
            cities.append({"id": ci.pk, "name": ci.name, "company": ci.company.pk})
        for building in buildings:
            js.append(
                {
                    "id": building.pk,
                    "city": building.city.pk,
                    "city_name": building.city.name,
                    "name": building.name,
                    "padez": building.padez,
                    "home_count": building.padez_home,
                    "status": 1 if building.status == True else 0,
                }
            )
        return render(
            request=request,
            template_name="home/create.html",
            context={
                "status": buildings.exists(),
                "city": buildings,
                "js": js,
                "company": Company.objects.all(),
                "cities": cities,
            },
        )
    return redirect("login")


def HomeEdit(request, id):
    if request.user.is_authenticated and request.user.username not in [
        "financeadmin",
        "receptionadmin",
    ]:
        if request.method == "POST":
            building_pk = request.POST.get("building_sel")
            name = request.POST.get("home")
            maydon = request.POST.get("maydon")
            price = request.POST.get("price")
            check = request.POST.get("check")
            floor = request.POST.get("floor")
            honalar = request.POST.get("honalar")
            number_str = str(maydon).replace(",", ".")
            
            home_instance = get_object_or_404(Home, pk=id)
            home_instance.home.home_number = name
            home_instance.home.field = float(number_str)
            home_instance.home.price = int(price)
            home_instance.home.home_floor = int(floor)
            home_instance.home.xona = honalar
            home_instance.home.busy = check == "on"
            home_instance.home.save()
            return redirect("homee")

        home_instance = get_object_or_404(Home, pk=id)
        buildings = Building.objects.all()
        return render(
            request=request,
            template_name="home/edit.html",
            context={
                "error": False,
                "building": buildings,
                "home": home_instance,
                "field": str(home_instance.home.field).replace(",", "."),
            },
        )

    return redirect("login")


def clean_phone_number(phone):
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 9:
        digits = "998" + digits
    
    return digits


def HomeUpload(request):
    if request.method == "POST":
        company = request.POST.get('company')
        city = request.POST.get('city')
        building_data = request.POST.get('building')
        file = request.FILES.get('file')
        b_select = Building.objects.filter(pk=building_data).first()

        if file:
            try:
                wb = openpyxl.load_workbook(file)
                sheet = wb.active
                padez_num = []
                
                for row in sheet.iter_rows(min_row=3, values_only=True):
                    try:
                        kv = row[2]  # Kvartira raqami
                        if not kv or not str(kv).strip().isdigit():
                            continue
                        kv = int(kv)
                        if kv == 0:
                            continue

                        podezd = int(row[3]) if row[3] and str(row[3]).strip().isdigit() else 1
                        etaj = int(row[4]) if row[4] and str(row[4]).strip().isdigit() else 1
                        xona = int(row[5]) if row[5] and str(row[5]).strip().isdigit() else 1

                        try:
                            m2 = float(str(row[6]).replace(' ', '')) if row[6] else 0
                        except (ValueError, TypeError):
                            m2 = 0
                            
                        try:
                            price_h = float(str(row[21]).replace(' ', '')) if row[21] else 0
                        except (ValueError, TypeError):
                            price_h = 0

                        home = HomeInformation.objects.create(
                            padez_number=podezd,
                            home_number=kv,
                            home_floor=etaj,
                            xona=xona,
                            price=price_h,
                            field=m2,
                            busy=False
                        )
                        
                        homei = Home.objects.create(building=b_select, home=home)

                        if row[7]:  # Shartnoma mavjudligini tekshirish
                            price_str = str(row[20]).replace(' ', '') if row[20] else '0'
                            try:
                                price = float(price_str)
                            except (ValueError, TypeError):
                                price = 0
                                
                            number1 = row[10] or ""
                            number2 = row[11] or ""
                            

                            client, created = ClientInformation.objects.get_or_create(
                                full_name=str(row[9] or ''),
                                phone=f"{clean_phone_number(number1)}, {clean_phone_number(number2)}",
                            )
                            
                            payment_str = str(row[22]).replace(' ', '') if row[22] else '0'
                            try:
                                payment = float(payment_str)
                            except (ValueError, TypeError):
                                payment = 0
                            
                            residual = price - payment

                            shartnoma = Client.objects.create(
                                client=client,
                                home=homei,
                                passport=f"{row[13] or ''} {row[14] or ''}".strip(),
                                passport_muddat=row[15] or None,
                                given=row[16] or '',
                                location=row[19] or '',
                                term=row[23] or 0,
                                home_price=price,
                                payment=payment,
                                residual=residual,
                                oylik_tolov=row[24] or 0,
                                count_month=row[23] or 0,
                                residu=0,
                                status="Rasmiylashtirilgan",
                                debt=True
                            )
                            creationdate = row[8].date()
                            created = datetime.combine(creationdate, shartnoma.created.time())
                            Rasrochka.objects.create(
                                    client=shartnoma,
                                    amount=row[22] or 0,
                                    amount_paid=row[22] or 0,
                                    qoldiq=0,
                                    month=0,
                                    date=created
                                )
                            
                            r_n = 1
                            for r in range(int(row[23])):
                                next_date = created.replace(month=(created.month + r - 1) % 12 + 1, year=created.year + (created.month + r - 1) // 12)
                                Rasrochka.objects.create(
                                    client=shartnoma,
                                    amount=row[24] or 0,
                                    amount_paid=0,
                                    qoldiq=0,
                                    month=r_n,
                                    date=next_date
                                )
                                r_n += 1
                            
                            home.busy = True
                            shartnoma.contract = str(row[7]).split("/")[0]
                            creationdate = row[8].date()
                            shartnoma.pay_date = row[8].date().day
                            shartnoma.created = datetime.combine(creationdate, shartnoma.created.time())
                            shartnoma.save()
                        
                        home.home_model_id = homei.pk
                        home.save()
                        padez_num.append(podezd)
                    
                    except Exception as e:
                        print(f"Error processing row: {row}")
                        print(f"Error details: {str(e)}")
                        continue
                
                if padez_num:
                    b_select.status = True
                    b_select.padez = max(padez_num)
                    b_select.save()
                
                messages.success(request, "Uylar muvaffaqiyatli qo'shildi")
                return redirect("homee")
            except Exception as e:
                messages.error(request, "Ma'lumotlarni yuklashda xatolik yuz berdi")
                print(e)
                return redirect("home-upload")
        else:
            messages.warning(request, "Fayl yuklashda xatolik yuz berdi")
            return redirect("home-upload")
    
    buildings = Building.objects.all()
    cities = [{"id": ci.pk, "name": ci.name, "company": ci.company.pk} for ci in City.objects.all()]
    js = [{
        "id": building.pk,
        "city": building.city.pk,
        "city_name": building.city.name,
        "name": building.name,
        "padez": building.padez,
        "home_count": building.padez_home,
        "status": 1 if building.status else 0,
    } for building in buildings]
    
    return render(request, "home/upload.html", {
        "status": buildings.exists(),
        "city": buildings,
        "js": js,
        "company": Company.objects.all(),
        "cities": cities,
    })


def HomeDelete(request, id):
    if request.user.is_authenticated and request.user.username not in [
        "financeadmin",
        "receptionadmin",
    ]:
        home_instance = get_object_or_404(Home, pk=id)
        home_instance.delete()
        return JsonResponse({"ok": True})

    return redirect("login")


## Client

async def send_sms(phone, sms: str):
    try:
        url = "https://notify.eskiz.uz/api/message/sms/send"
        params = {
            "mobile_phone": f"{phone}",
            "message": f"{sms}",
            "from": "4546",
        }
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Mzg3Mzk1ODIsImlhdCI6MTczNjE0NzU4Miwicm9sZSI6InVzZXIiLCJzaWduIjoiZmY4Mzk1ZDBjOWE2NmIzYjEzYjkzODUxNzU1Njc2NDZhMzc0NGVlMThiMDM0MjNlYmJlYTZlOTc5NjNjNGM1OSIsInN1YiI6Ijc3NTkifQ.dk7T_wtpYnDpTvEqN81JIwaURhN_t3mTihWDhfxIe64",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, data=params, headers=headers, ssl=False
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print("SMS yuborildi, javob:", data)
                else:
                    print(
                        f"SMS yuborishda xatolik:\nstatus: {response.status}\njavob: {await response.text()}"
                    )
    except Exception as e:
        print("Xatolik:", e)


def ClientPage(request):
    if request.user.is_authenticated and request.user.username != "financeadmin":
        if request.method == "POST":
            action = request.POST.get("action")
            if action == "search":
                search = request.POST.get("search")
                clients = ClientInformation.objects.filter(
                    full_name__icontains=search
                ).order_by("-created")

                return render(
                    request=request,
                    template_name="client/client.html",
                    context={"client": clients, "search_value": search},
                )
            elif action == "sms":
                sms = request.POST.get("sms-text")
                clients = ClientInformation.objects.order_by("-created")
                for client in clients:
                    try:
                        asyncio.run(send_sms(client.phone, sms))
                    except Exception as e:
                        continue

            else:
                clients = ClientInformation.objects.order_by("-created")
                return render(
                    request=request,
                    template_name="client/client.html",
                    context={"client": clients},
                )

        filter = request.GET.get("filter")
        if filter and filter.isdigit() and filter in ["0", "1", "2", "3", "4"]:
            status_map = {
                "0": "Telegramda",
                "1": "Instagramda",
                "2": "YouTubeda",
                "3": "Odamlar orasida",
                "4": "Xech qayerda",
            }
            clients = ClientInformation.objects.filter(
                heard=status_map[filter]
            ).order_by("-created")
        else:
            clients = ClientInformation.objects.order_by("-created")
        return render(
            request=request,
            template_name="client/client.html",
            context={"client": clients},
        )

    return redirect("login")


def ClientCreate(request):
    if request.user.is_authenticated and request.user.username not in [
        "financeadmin",
    ]:
        if request.method == "POST":
            full_name = request.POST.get("full_name")
            phone = request.POST.get("phone")
            heard = request.POST.get("heard")

            if full_name and phone and heard:
                try:
                    phone = int(phone)
                    ClientInformation.objects.create(
                        full_name=full_name, phone=phone, heard=heard
                    )
                    messages.success(request, "Client successfully created.")
                    return redirect("client")
                except ValueError:
                    messages.error(request, "Invalid phone number.")
            else:
                messages.error(request, "All fields are required.")

        return render(request=request, template_name="client/create.html")

    return redirect("login")


def ClientDelete(request, id):
    if request.user.is_authenticated and request.user.username not in ["financeadmin"]:
        client_instance = get_object_or_404(ClientInformation, pk=id)
        contract = Client.objects.filter(client=client_instance)
        if contract.exists():
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Mijozni olib tashlash mumkin emas. Sababi bu mijoz nomiga xonadan rasmiylashtirilgan.",
                }
            )
        else:
            client_instance.delete()
            return JsonResponse(
                {"ok": True, "message": "Mijoz muvaffaqiyatli o'chirildi."}
            )

    return redirect("login")


def ClientEdit(request, id):
    if request.user.is_authenticated and request.user.username not in ["financeadmin"]:
        client_instance = get_object_or_404(ClientInformation, pk=id)

        if request.method == "POST":
            name = request.POST.get("full_name")
            phone = request.POST.get("phone")
            heard = request.POST.get("heard")

            try:
                client_instance.full_name = name
                client_instance.phone = int(phone)  # Ensure phone is an integer
                client_instance.heard = heard
                client_instance.save()
                messages.success(request, "Client information updated successfully.")
                return redirect("client")
            except ValueError:
                messages.error(request, "Invalid phone number.")

        return render(
            request=request,
            template_name="client/edit.html",
            context={"error": False, "client": client_instance},
        )

    return redirect("login")


## Contract

def RasrochkaPage(request):
    if request.method == "POST":
        try:
            amount = request.POST.get("amount")
            client_id = request.POST.get("debt-id")

            if not amount or not client_id:
                messages.error(request, "Kerakli ma'lumotlar yetarli emas.")
                return redirect(f"contract")

            client = get_object_or_404(Client, pk=client_id)

            if client.debt:
                try:
                    amount = int(amount)
                    oylik_tolov = int(client.oylik_tolov)

                    # Calculate full months that can be paid
                    full_months = amount // oylik_tolov
                    remaining_amount = amount % (client.residual)

                    Rasrochka.objects.create(
                        client=client,
                        residue=client.residual - amount,
                        amount=amount,
                    )
                    client.count_month -= 1
                    client.residual -= amount
                    
                    if client.residual <= 0:
                        client.status = "Tugallangan"
                        client.debt = False
                        client.residual = 0
                        client.residu = 0

                    client.save()

                    # Use asyncio.create_task() if inside an async function
                    asyncio.run(
                        send_sms(
                            phone=client.client.phone,
                            sms=f"Hurmatli {client.client.full_name}. #00{client.pk} raqamli shartnoma bo'yicha qilgan to'lovingiz qabul qilindi. To'lov miqdori: {amount} so'm. Shartnoma bo'yicha qolgan to'lov miqdori: {client.residual - client.residu} so'm.",
                        )
                    )
                    print(
                        f"Hurmatli {client.client.full_name}. #00{client.pk} raqamli shartnoma bo'yicha qilgan to'lovingiz qabul qilindi. To'lov miqdori: {amount} so'm. Shartnoma bo'yicha qolgan to'lov miqdori: {client.residual - client.residu} so'm."
                    )

                    return redirect(f"contract")
                except ValueError:
                    messages.error(request, "Summa noto'g'ri kiritildi.")
        except Exception as e:
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
    return redirect(f"contract")

from datetime import datetime, date
def contract_payment(request):
    """Handle payment from the contract list page"""
    if request.method == "POST" and request.user.is_authenticated:
        contract_id = request.POST.get("contract-id")
        custom_amount = request.POST.get("customAmount")
        
        if not contract_id or not custom_amount:
            messages.warning(request, "To'lov ma'lumotlari to'liq emas")
            return redirect("contract")
        
        try:
            contract = Client.objects.get(pk=contract_id)
            custom_amount = int(custom_amount)
            
            # Call the custom payment handler
            return handle_custom_payment(request, contract, contract_id)
        except Client.DoesNotExist:
            messages.warning(request, "Shartnoma topilmadi")
        except ValueError:
            messages.warning(request, "To'lov miqdori noto'g'ri formatda")
    
    return redirect("contract")

def ContractPage(request):
    if request.user.is_authenticated and request.user.username != "financeadmin":

        # Handle payment POST request
        if request.method == "POST":
            payment_type = request.POST.get("payment-type")
            
            if payment_type == "custom":
                contract_id = request.POST.get("contract-id")
                custom_amount = request.POST.get("customAmount")
                
                if not contract_id or not custom_amount:
                    messages.warning(request, "To'lov ma'lumotlari to'liq emas")
                else:
                    try:
                        contract = Client.objects.get(pk=contract_id)
                        custom_amount = int(custom_amount)
                        
                        # Process the payment directly here instead of redirecting
                        # Find the first unpaid month
                        rasrochka_entries = Rasrochka.objects.filter(client=contract, qoldiq__gt=0).order_by('month')
                        
                        if rasrochka_entries.exists():
                            remaining_amount = custom_amount
                            
                            for entry in rasrochka_entries:
                                if remaining_amount <= 0:
                                    break
                                    
                                # Calculate how much we can pay for this month
                                payment_for_this_month = min(remaining_amount, entry.qoldiq)
                                
                                # Update the payment record
                                entry.amount_paid += payment_for_this_month
                                entry.qoldiq = entry.amount - entry.amount_paid
                                entry.save()
                                
                                # Reduce the remaining amount
                                remaining_amount -= payment_for_this_month
                        
                        # Check if there are any unpaid amounts
                        rasrochka_entries = Rasrochka.objects.filter(client=contract)
                        total_remaining = rasrochka_entries.aggregate(Sum('qoldiq'))['qoldiq__sum'] or 0
                        
                        # Update the contract's debt status
                        contract.debt = total_remaining > 0
                        
                        # If there's no remaining debt, mark the contract as completed
                        if total_remaining == 0 and contract.status == "Rasmiylashtirilgan":
                            contract.status = "Tugallangan"
                        
                        contract.save()
                        
                        messages.success(request, f"{custom_amount} so'm miqdorida to'lov muvaffaqiyatli amalga oshirildi")
                    except Client.DoesNotExist:
                        messages.warning(request, "Shartnoma topilmadi")
                    except ValueError:
                        messages.warning(request, "To'lov miqdori noto'g'ri formatda")

        # Continue with the regular GET request handling
        q = request.GET.get("q")
        city_id = request.GET.get("city")
        building_id = request.GET.get("building")
        debt_status = request.GET.get("debt")
        status = request.GET.get("status")
        company_id = request.GET.get("company")
        filters = {}

        contract_queryset = Client.objects.all()

        if company_id:
            filters["home__building__city__company__id"] = company_id
        if city_id:
            filters["home__building__city__id"] = city_id
        if building_id:
            filters["home__building__id"] = building_id
        if debt_status:
            filters["debt"] = debt_status
        if status and status in ["0", "1", "2", "3"]:
            status_map = {
                "0": "Bekor qilingan",
                "1": "Rasmiylashtirilmoqda",
                "2": "Rasmiylashtirilgan",
                "3": "Tugallangan",
            }
            filters["status"] = status_map[status]
        if filters:
            contract_queryset = Client.objects.filter(**filters)

        if q:
            contract_queryset = Client.objects.filter(passport__icontains=q).all()

        # Get all contracts with payment information
        contracts_with_payments = []
        for c in contract_queryset.order_by("-created"):
            # Get all Rasrochka entries for this contract
            rasrochka_entries = Rasrochka.objects.filter(client=c).order_by("date")
            
            # Calculate payment information
            total_amount = rasrochka_entries.aggregate(Sum('amount'))['amount__sum'] or 0
            total_paid = rasrochka_entries.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
            total_remaining = rasrochka_entries.aggregate(Sum('qoldiq'))['qoldiq__sum'] or 0
            
            # Get initial payment (month 0)
            initial_payment = rasrochka_entries.filter(month=0).first()
            initial_payment_amount = initial_payment.amount if initial_payment else 0
            
            # Get monthly payment (first regular month)
            monthly_payment = rasrochka_entries.filter(month__gt=0).first()
            monthly_payment_amount = monthly_payment.amount if monthly_payment else 0
            
            # Get next unpaid month
            next_unpaid = rasrochka_entries.filter(qoldiq__gt=0).order_by('month').first()
            next_unpaid_month = next_unpaid.month if next_unpaid else None
            next_unpaid_amount = next_unpaid.qoldiq if next_unpaid else 0
            
            # Count remaining months to pay
            remaining_months = rasrochka_entries.filter(qoldiq__gt=0).count()
            
            # Check if contract is in debt (has any remaining balance)
            is_in_debt = total_remaining > 0
            
            # Update the contract's debt status and completion status in the database if needed
            needs_update = False
            
            if c.debt != is_in_debt:
                c.debt = is_in_debt
                needs_update = True
            
            # If there's no remaining debt and the contract is not completed yet, mark it as completed
            if total_remaining == 0 and c.status == "Rasmiylashtirilgan":
                c.status = "Tugallangan"
                needs_update = True
            
            if needs_update:
                c.save()
            
            # Add payment information to contract
            c.payment_info = {
                'initial_payment': initial_payment_amount,
                'total_amount': total_amount,
                'total_paid': total_paid,
                'total_remaining': total_remaining,
                'monthly_payment': monthly_payment_amount,
                'next_unpaid_month': next_unpaid_month,
                'next_unpaid_amount': next_unpaid_amount,
                'remaining_months': remaining_months,
                'is_in_debt': is_in_debt
            }
            
            contracts_with_payments.append(c)

        # Prepare filter options
        city_l = [{"name": "Barchasi", "url": "?"}] + [
            {"name": city.name, "url": f"?city={city.pk}"}
            for city in City.objects.all()
        ]

        building_l = [{"name": "Barchasi", "url": "?"}] + [
            {
                "name": f"{building.city.name} -> {building.name}",
                "url": f"?building={building.pk}",
            }
            for building in Building.objects.all()
        ]

        company = Company.objects.all()

        home_filter = []
        index = 0
        c_index = 0
        for i in company:
            home_filter.append(
                {"company": i.name, "url": f"?company={i.pk}", "city": []}
            )
            for x in City.objects.filter(company=i):
                home_filter[index]["city"].append(
                    {"name": x.name, "url": f"?city={x.pk}", "building": []}
                )
                building = Building.objects.filter(city=x)
                if building.exists():
                    for l in building:
                        home_filter[index]["city"][c_index]["building"].append(
                            {"name": l.name, "url": f"?building={l.pk}"}
                        )
                else:
                    home_filter[index]["city"][c_index]["building"].append(
                        {"name": "Binolar yo'q", "url": "", "content": "disabled"}
                    )
                c_index += 1
            c_index = 0
            index += 1

        return render(
            request=request,
            template_name="contract/contract.html",
            context={
                "contract": contracts_with_payments,
                "city_filter": city_l,
                "building_filter": building_l,
                "home_filter": home_filter,
                "companies": Company.objects.all(),
                "cities": City.objects.all(),
                "buildings": Building.objects.all(),
            },
        )

    return redirect("login")

def ContractCreate(request):
    if request.user.is_authenticated and request.user.username != "financeadmin":
        if request.method == "POST":
            # Extract form data
            company_sel = request.POST.get("company_sel")
            city_sel = request.POST.get("city_sel")
            building_sel = request.POST.get("building_sel")
            padez_sel = request.POST.get("padez_sel")
            selected_home = request.POST.get("selected_home")
            client_name = request.POST.get("client_name")
            client_phone = request.POST.get("client_phone")
            client_passport = request.POST.get("client_passport")
            muddat = request.POST.get("muddat")
            olingan = request.POST.get("olingan")
            location = request.POST.get("location")
            client_payment = request.POST.get("client_payment")
            client_adp = request.POST.get("client_adp")
            status = request.POST.get("status")
            pay_date = request.POST.get("pay_date")
            kvm = request.POST.get("kvm")

            # Validate numeric fields
            try:
                client_phone = int(client_phone)
                client_payment = int(client_payment)
                client_adp = int(client_adp)
                pay_date = int(pay_date)
            except ValueError:
                messages.error(
                    request,
                    "Telefon raqami, to'lov muddati, avans to'lovi va to'lov sanasi raqam bo'lishi kerak.",
                )
                return redirect("contract_create")

            # Find the selected home
            homee = Home.objects.filter(
                building=building_sel,
                home__padez_number=padez_sel,
                home__home_number=selected_home,
            )
            
            if not homee.exists():
                messages.error(request, "Tanlangan uy topilmadi.")
                return redirect("contract_create")
                
            home = homee.first()
            
            # Update home price if it has changed
            if kvm and home.home.price != kvm:
                home.home.price = kvm
                home.home.save()
                
            # Find or create client
            mijoz = ClientInformation.objects.filter(
                full_name=client_name, phone=client_phone
            )
            if mijoz.exists():
                client = mijoz.first()
            else:
                client = ClientInformation.objects.create(
                    full_name=client_name, phone=client_phone
                )

            # Calculate total price
            total_price = float(home.home.field) * int(home.home.price)
            
            # Process payment terms
            if client_payment != 0:
                if client_adp != 0:
                    # Full payment case
                    if client_adp == total_price:
                        contract = Client.objects.create(
                            client=client,
                            home=home,
                            passport=client_passport,
                            term=0,
                            payment=client_adp,
                            residual=0,
                            oylik_tolov=0,
                            count_month=0,
                            residu=0,
                            status="Tugallangan",
                            debt=False,
                        )
                        Rasrochka.objects.create(
                            client=contract, amount=client_adp, month=0, amount_paid=client_adp, qoldiq=0, date=datetime.now()
                        )
                    else:
                        # Installment payment case
                        res = total_price - client_adp
                        cp = client_payment
                        exact_result = res / cp
                        
                        # Round down to nearest 100,000
                        rounded_result = math.floor(exact_result / 100000) * 100000

                        contract = Client.objects.create(
                            client=client,
                            home=home,
                            passport=client_passport,
                            term=client_payment,
                            payment=client_adp,
                            residual=res,
                            oylik_tolov=rounded_result,
                            count_month=client_payment,
                            residu=0,
                            status=status,
                            debt=True,
                        )
                        
                        # Create initial payment record
                        rmd = Rasrochka.objects.create(
                            client=contract,
                            amount=client_adp,
                            month=0, 
                            amount_paid=client_adp,
                            qoldiq=0,
                            date=datetime.now()
                        )
                        
                        # Set the start date for installments
                        start_date = datetime.now().replace(day=pay_date)
                        if start_date.day < datetime.now().day:
                            start_date += timedelta(days=32)
                        start_date = start_date.replace(day=pay_date)

                        # Create monthly payment records
                        remaining = res
                        for month in range(1, client_payment + 1):
                            if month == client_payment:  # Last payment
                                amount = remaining
                            else:
                                amount = min(rounded_result, remaining)
                            
                            payment_date = (start_date + timedelta(days=32 * month)).replace(day=pay_date)
                            
                            rms = Rasrochka.objects.create(
                                client=contract,
                                amount=amount,
                                month=month, 
                                amount_paid=0,
                                qoldiq=amount,
                                date=payment_date
                            )
                            
                            remaining -= amount

                        # Update contract with final values
                        contract.oylik_tolov = rounded_result
                        contract.save()
                else:
                    # No initial payment case
                    res = total_price
                    cp = client_payment
                    exact_result = res / cp
                    rounded_result = math.floor(exact_result / 100000) * 100000
                    
                    contract = Client.objects.create(
                        client=client,
                        home=home,
                        passport=client_passport,
                        term=client_payment,
                        payment=0,
                        residual=res,
                        oylik_tolov=rounded_result,
                        count_month=client_payment,
                        residu=0,
                        status=status,
                        debt=True,
                    )
                    
                    # Set the start date for installments
                    start_date = datetime.now().replace(day=pay_date)
                    if start_date.day < datetime.now().day:
                        start_date += timedelta(days=32)
                    start_date = start_date.replace(day=pay_date)

                    # Create monthly payment records
                    remaining = res
                    for month in range(1, client_payment + 1):
                        if month == client_payment:  # Last payment
                            amount = remaining
                        else:
                            amount = min(rounded_result, remaining)
                        
                        payment_date = (start_date + timedelta(days=32 * month)).replace(day=pay_date)
                        
                        rms = Rasrochka.objects.create(
                            client=contract,
                            amount=amount,
                            month=month, 
                            amount_paid=0,
                            qoldiq=amount,
                            date=payment_date
                        )
                        
                        remaining -= amount

                    # Update contract with final values
                    contract.oylik_tolov = rounded_result
                    contract.save()
                
                # Mark home as busy (sold)
                home.home.busy = True
                home.home.save()
            else:
                # Zero payment term case (full payment)
                if client_adp == total_price:
                    contract = Client.objects.create(
                        client=client,
                        home=home,
                        passport=client_passport,
                        term=0,
                        payment=client_adp,
                        residual=0,
                        oylik_tolov=0,
                        count_month=0,
                        residu=0,
                        status="Tugallangan",
                        debt=False,
                    )
                    Rasrochka.objects.create(
                        client=contract,
                        amount=client_adp,
                        month=0, 
                        amount_paid=client_adp,
                        qoldiq=0,
                        date=datetime.now()
                    )
                    home.home.busy = True
                    home.home.save()
                else:
                    messages.error(request, "To'lov muddati 0 bo'lsa, to'liq to'lov qilinishi kerak.")
                    return redirect("contract_create")
                    
            # Update additional contract details
            contract.passport_muddat = muddat
            contract.given = olingan
            contract.location = location
            contract.pay_date = pay_date
            contract.save()

            messages.success(request, "Shartnoma muvaffaqiyatli yaratildi.")
            return redirect("contract")

        # GET request handling
        city = City.objects.all()
        building = Building.objects.all()
        home = Home.objects.all()

        data = {"city": [], "building": [], "home": []}

        for i in city:
            data["city"].append({"id": i.pk, "name": i.name, "company": i.company.pk})
        for x in building:
            data["building"].append(
                {
                    "id": x.pk,
                    "name": x.name,
                    "city": x.city.pk,
                    "padez": x.padez,
                    "padez_home": x.padez_home,
                    "floor": x.floor,
                    "status": "true" if x.status else "false",
                }
            )

        for y in home:
            data["home"].append(
                {
                    "id": y.pk,
                    "building": y.building.pk,
                    "home": y.home.pk,
                    "padez_number": y.home.padez_number,
                    "home_number": y.home.home_number,
                    "home_floor": y.home.home_floor,
                    "field": y.home.field,
                    "price": y.home.price,
                    "busy": "true" if y.home.busy else "false",
                    "home_model_id": y.home.home_model_id or "",
                }
            )

        return render(
            request=request,
            template_name="contract/create.html",
            context={
                "city": city,
                "building": building,
                "home": home,
                "result": data,
                "company": Company.objects.all(),
            },
        )
    return redirect("login")
def ContractEdit(request, id):
    if request.user.is_authenticated and request.user.username != "financeadmin":
        contract = get_object_or_404(Client, pk=id)
        if request.method == "POST":
            full_name = request.POST.get("full_name")
            phone = request.POST.get("phone")
            passport = request.POST.get("passport")
            status = request.POST.get("status")
            contract.passport = passport
            client = ClientInformation.objects.filter(full_name=full_name, phone=phone)
            if client.exists():
                contract.client.full_name = full_name
                contract.client.phone = phone
            else:
                client_create = ClientInformation.objects.create(
                    full_name=full_name, phone=phone
                )
                contract.client = client_create
            contract.client.save()
            if str(status) == "Tugallangan":
                contract.debt = False
                contract.residual = 0
                contract.residu = 0
                contract.count_month = 0

                Rasrochka.objects.create(
                        client=contract,
                        amount=contract.residual,
                        month=0, amount_paid=contract.residual
                )
            if str(status) == "Bekor qilingan":
                contract.debt = False
                contract.residual = 0
                contract.residu = 0
                contract.count_month = 0

            contract.status = status
            contract.save()
            return redirect("contract")

        return render(
            request=request,
            template_name="contract/edit.html",
            context={"contract": contract},
        )


def ContractDelete(request, id):
    if request.user.is_authenticated and request.user.username not in [
        "financeadmin",
        "receptionadmin",
    ]:
        client_instance = get_object_or_404(Client, pk=id)

        client_instance.home.home.busy = False
        client_instance.home.home.save()

        ClientTrash.objects.create(
            client=client_instance.client,
            home=client_instance.home,
            passport=client_instance.passport,
            term=client_instance.term,
            payment=client_instance.payment,
            residual=client_instance.residual,
            oylik_tolov=client_instance.oylik_tolov,
            count_month=client_instance.count_month,
            status=client_instance.status,
            debt=client_instance.debt,
            created=client_instance.created,
        )

        client_instance.delete()
        return JsonResponse({"ok": True})

    return redirect("login")


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Client, Rasrochka
from django.db.models import Sum
from datetime import datetime

def JadvalPage(request, id):
    if request.user.is_authenticated and request.user.username not in {"financeadmin"}:
        contract = get_object_or_404(Client, pk=id)
        rasrochka = Rasrochka.objects.filter(client=contract).order_by("date")
        home_price = contract.home.home.price * contract.home.home.field
        
        # Handle POST requests (payments)
        if request.method == "POST":
            payment_type = request.POST.get("payment-type")
            
            # Handle monthly payment
            if payment_type == "monthly":
                return handle_monthly_payment(request, contract, id)
            # Handle custom payment (any amount)
            elif payment_type == "custom":
                return handle_custom_payment(request, contract, id)
            
            else:
                messages.warning(request, "To'lov turi aniqlanmadi")
        
        # Render the payment schedule page
        return render(
            request,
            "contract/list.html",
            {
                "contract": contract,
                "rasrochka": rasrochka,
                "price": home_price,
                "pk": id
            },
        )

    return redirect("login")

def handle_monthly_payment(request, contract, contract_id):
    """Handle payment for a specific month"""
    debt_id = request.POST.get("debt-id")
    summa = request.POST.get("amount")
    
    if not debt_id or not summa:
        messages.warning(request, "To'lov ma'lumotlari to'liq emas")
        return render(
            request,
            "contract/list.html",
            {
                "contract": contract,
                "rasrochka": Rasrochka.objects.filter(client=contract).order_by("date"),
                "price": contract.home.home.price * contract.home.home.field,
                "pk": contract_id
            },
        )
    
    rasrorchka_obj = Rasrochka.objects.filter(pk=debt_id)
    
    if rasrorchka_obj.exists():
        value = rasrorchka_obj.first()
        
        if value.client:
            # Add the payment amount to the existing amount_paid
            value.amount_paid += int(summa)
            value.pay_date = datetime.now()
            value.save()
            
            messages.success(request, "To'lov muvaffaqiyatli qabul qilindi")
            return render(
                request,
                "contract/list.html",
                {
                    "contract": contract,
                    "rasrochka": Rasrochka.objects.filter(client=contract).order_by("date"),
                    "price": contract.home.home.price * contract.home.home.field,
                    "pk": contract_id
                },
            )
    
    messages.warning(request, "Xonadon haqida ma'lumotlar aniqlanmadi")
    return render(
        request,
        "contract/list.html",
        {
            "contract": contract,
            "rasrochka": Rasrochka.objects.filter(client=contract).order_by("date"),
            "price": contract.home.home.price * contract.home.home.field,
            "pk": contract_id
        },
    )

def handle_custom_payment(request, contract, contract_id):
    """
    Handle custom payment of any amount (minimum 1 soum).
    This distributes the payment across multiple months automatically.
    """
    custom_amount = int(request.POST.get("customAmount", 0))
    
    if custom_amount < 1:
        messages.warning(request, "To'lov miqdori kamida 1 so'm bo'lishi kerak")
        return render(
            request,
            "contract/list.html",
            {
                "contract": contract,
                "rasrochka": Rasrochka.objects.filter(client=contract).order_by("date"),
                "price": contract.home.home.price * contract.home.home.field,
                "pk": contract_id
            },
        )
    
    # Get all unpaid months ordered by date
    unpaid_months = Rasrochka.objects.filter(
        client=contract, 
        qoldiq__gt=0
    ).order_by("date")
    
    if not unpaid_months.exists():
        messages.warning(request, "Barcha to'lovlar to'langan")
        return render(
            request,
            "contract/list.html",
            {
                "contract": contract,
                "rasrochka": Rasrochka.objects.filter(client=contract).order_by("date"),
                "price": contract.home.home.price * contract.home.home.field,
                "pk": contract_id
            },
        )
    
    remaining_amount = custom_amount
    payments_made = 0
    last_month_paid = None
    
    # Distribute payment across months
    for month in unpaid_months:
        if remaining_amount <= 0:
            break
        
        # Calculate how much to pay for this month
        amount_to_pay = min(remaining_amount, month.qoldiq)
        
        # Update the month's payment
        month.amount_paid += amount_to_pay
        month.pay_date = datetime.now()
        month.save()
        
        # Reduce the remaining amount
        remaining_amount -= amount_to_pay
        payments_made += 1
        last_month_paid = month
    
    # Success message showing how many months were covered
    if payments_made > 0:
        if last_month_paid and last_month_paid.qoldiq > 0:
            messages.success(
                request, 
                f"To'lov muvaffaqiyatli qabul qilindi. {last_month_paid.month}-oy uchun qolgan qarz: {last_month_paid.qoldiq:,} so'm"
            )
        else:
            messages.success(request, f"To'lov muvaffaqiyatli qabul qilindi")
    else:
        messages.warning(request, "To'lov qabul qilinmadi")
    
    return render(
        request,
        "contract/list.html",
        {
            "contract": contract,
            "rasrochka": Rasrochka.objects.filter(client=contract).order_by("date"),
            "price": contract.home.home.price * contract.home.home.field,
            "pk": contract_id
        },
    )
    
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from .models import Client, Rasrochka
from django.db.models import Sum
from datetime import datetime
import tempfile
import os


def JadvalDownload(request, id):
    contract = get_object_or_404(Client, pk=id)
    rasrochka = Rasrochka.objects.filter(client=contract).order_by('month')

    # Calculate total price and payments
    total_price = contract.home.home.field * contract.home.home.price
    down_payment = contract.payment
    remaining_balance = total_price - down_payment
    down_payment_percentage = (down_payment / total_price) * 100

    # O'zbek tilidagi oylar nomlari (lotin alifbosida)
    month_names_uz = {
        1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel", 5: "may", 6: "iyun",
        7: "iyul", 8: "avgust", 9: "sentabr", 10: "oktabr", 11: "noyabr", 12: "dekabr"
    }

    # Generate payment schedule
    pay_list = []
    current_balance = remaining_balance
    
    for i in rasrochka:
        if i.month > 0:  # Skip initial payment
            month_date = i.date
            payment_amount = min(i.amount, current_balance)  # Ensure payment doesn't exceed current balance
            
            if current_balance > 0:
                pay_list.append({
                    "number": i.month,
                    "day": contract.pay_date,
                    "month": month_names_uz[month_date.month],
                    "year": month_date.year,
                    "payment": "{:,}".format(payment_amount).replace(",", " "),
                    "remaining": "{:,}".format(max(0, current_balance - payment_amount)).replace(",", " ")
                })
                current_balance = max(0, current_balance - payment_amount)
            else:
                # If balance is already 0, add remaining months with 0 payment
                pay_list.append({
                    "number": i.month,
                    "day": contract.pay_date,
                    "month": month_names_uz[month_date.month],
                    "year": month_date.year,
                    "payment": "0",
                    "remaining": "0"
                })

    # Prepare context for the template
    context = {
        'contract': contract,
        'total_price': "{:,}".format(total_price).replace(",", " "),
        'down_payment': "{:,}".format(down_payment).replace(",", " "),
        'remaining_balance': "{:,}".format(remaining_balance).replace(",", " "),
        'down_payment_percentage': round(down_payment_percentage),
        'pay_list': pay_list,
        'company': contract.home.building.city.company
    }

    # Render the HTML template
    html_string = render_to_string('list.html', context)

    # CSS styles (unchanged)
    css_string = """
        @page {
            size: A4;
            margin: 1.5cm;  /* Sahifa chetlarini kamaytirdik */
        }
        body {
            font-family: "Times New Roman", Times, serif;
            font-size: 10px;  /* Asosiy matn shriftini kichikroq qildik */
            line-height: 1.2;  /* Qatorlar orasidagi masofani kamaytirdik */
        }
        .title {
            font-size: 14px;  /* Sarlavha shriftini kichikroq qildik */
            text-align: center;
            font-weight: bold;
            margin-bottom: 10px;  /* Sarlavha ostidagi bo'sh joyni kamaytirdik */
        }
        .header-info {
            margin-bottom: 10px;  /* Ma'lumotlar orasidagi bo'sh joyni kamaytirdik */
        }
        .amount {
            color: red;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;  /* Jadval ostidagi bo'sh joyni kamaytirdik */
        }
        th, td {
            border: 1px solid black;
            padding: 1px;  /* Katakchalar ichidagi bo'sh joyni kamaytirdik */
            text-align: center;
            font-size: 9px;  /* Jadval ichidagi matn shriftini kichikroq qildik */
        }
        th {
            background-color: #f2f2f2;
        }
        .total-row {
            font-weight: bold;
        }
        .signature {
            margin-top: 15px;  /* Imzo qismini jadvalga yaqinroq qildik */
        }
        .signature-line {
            display: flex;
            justify-content: space-between;
        }
    """

 

    # Configure Weasyprint
    font_config = FontConfiguration()
    html = HTML(string=html_string)
    css = CSS(string=css_string, font_config=font_config)

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        # Generate PDF and save to temporary file
        html.write_pdf(target=tmp.name, stylesheets=[css], font_config=font_config)

    # Prepare the response
    response = FileResponse(open(tmp.name, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="tolov_grafigi_{id}.pdf"'

    # Delete the temporary file after sending the response
    def delete_file(sender, **kwargs):
        os.unlink(tmp.name)
    
    response.close = delete_file

    return response
def BuildingInformation(request):
    if request.user.is_authenticated and (
        request.user.username != "financeadmin"
        or request.user.username != "receptionadmin"
    ):
        city = City.objects.all()
        building = Building.objects.all()
        home = Home.objects.all()
        client = Client.objects.all()
        data = {"city": [], "building": [], "home": [], "client": []}
        for i in city:
            data["city"].append({"id": i.pk, "name": i.name, "company": i.company.pk})
        for x in building:
            data["building"].append(
                {
                    "id": x.pk,
                    "name": x.name,
                    "city": x.city.pk,
                    "padez": x.padez,
                    "padez_home": x.padez_home,
                    "floor": x.floor,
                    "status": "true" if x.status else "false",
                }
            )

        for y in home:
            data["home"].append(
                {
                    "id": y.pk,
                    "building": y.building.pk,
                    "home": y.home.pk,
                    "padez_number": y.home.padez_number,
                    "home_number": y.home.home_number,
                    "home_floor": y.home.home_floor,
                    "field": y.home.field,
                    "price": y.home.price,
                    "busy": "true" if y.home.busy else "false",
                }
            )
        for v in client:
            data["client"].append(
                {
                    "id": v.pk,
                    "client_name": v.client.full_name,
                    "client_phone": v.client.phone,
                    "client_passport": v.passport,
                    "home": v.home.pk,
                    "building": v.home.building.pk,
                    "padez_number": v.home.home.padez_number,
                    "home_number": v.home.home.home_number,
                }
            )
        return render(
            request=request,
            template_name="building/information.html",
            context={
                "city": city,
                "building": building,
                "home": home,
                "result": data,
                "company": Company.objects.all(),
            },
        )
    return redirect("login")


def Statistika(request):
    start = datetime(2024, 10, 1)
    month_name = [
        "Yanvar",
        "Fevral",
        "Mart",
        "Aprel",
        "May",
        "Iyun",
        "Iyul",
        "Avgust",
        "Sentabr",
        "Oktabr",
        "Noyabr",
        "Dekabr",
    ]

    hozirgi_oy = datetime.now().replace(day=1)
    oylar = []

    # Start from the launch date
    oy = start
    while oy <= hozirgi_oy:
        oylar.append(oy)
        oy = (oy + timedelta(days=32)).replace(day=1)
    month_list = []
    number = 1
    for oy_boshi in oylar:
        oy_oxiri = (oy_boshi + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        month = datetime.strptime(str(oy_boshi), "%Y-%m-%d %H:%M:%S").date()
        month_list.append(
            {
                "number": number,
                "month": f"{month_name[month.month - 1]}. {month.year} - yil",
                "url": f"/statistics/download/{oy_boshi.date()}:::{oy_oxiri.date()}/",
            }
        )
        number += 1

    return render(
        request=request,
        template_name="statistics.html",
        context={"month_list": month_list},
    )


def StatisticsDownloadAll(request):
    start = datetime(2024, 10, 1)
    month_name = [
        "Yanvar",
        "Fevral",
        "Mart",
        "Aprel",
        "May",
        "Iyun",
        "Iyul",
        "Avgust",
        "Sentabr",
        "Oktabr",
        "Noyabr",
        "Dekabr",
    ]

    hozirgi_oy = datetime.now().replace(day=1)
    oylar = []

    # Oylarni yaratish
    oy = start
    while oy <= hozirgi_oy:
        oylar.append(oy)
        oy = (oy + timedelta(days=32)).replace(day=1)

    # Hisobot ma'lumotlarini tayyorlash
    month_list = []
    number = 1
    for oy_boshi in oylar:
        oy_oxiri = (oy_boshi + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        contracts = Client.objects.filter(created__date__range=(oy_boshi, oy_oxiri))
        oylik_tushum = 0
        for contract in contracts:
            rasrochka = Rasrochka.objects.filter(
                client=contract, date__date__range=(oy_boshi, oy_oxiri)
            )
            for i in rasrochka:
                oylik_tushum += i.amount
        month = datetime.strptime(str(oy_boshi), "%Y-%m-%d %H:%M:%S").date()
        month_list.append(
            [number, f"{month_name[month.month - 1]} {month.year}-yil", oylik_tushum]
        )
        number += 1

    # HTML tarkibini tayyorlash
    html_content = """
    <html>
        <head>
            <style>
            .title{
                font-size: 22px;
               text-align: center;
               border-bottom: 1px solid black;
                      font-family: "Times New Roman", Times, serif;
            }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: center;
                    font-size: 17px;
                      font-family: "Times New Roman", Times, serif;
                }
                th {
                    background-color: #f2f2f2;
                }
                .n{
                    width: 20%
                }
                 .m{
                    width: 40%
                }
                 .i{
                    width: 40%
                }
            </style>
        </head>
        <body>
            <h2 class="title">Oylik Tushum Hisoboti</h2>
            
            
            <table>
                <thead>
                    <tr>
                        <th class="n">N</th>
                        <th class="m">Oy kesimi</th>
                        <th class="i">Tushum (so'm)</th>
                    </tr>
                </thead>
                <tbody>
    """

    for row in month_list:
        html_content += f"""
                    <tr>
                        <td>{row[0]}</td>
                        <td>{row[1]}</td>
                        <td>{row[2]:,}</td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </body>
    </html>
    """

    # PDFni yaratish
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="oylik_tushum.pdf"'

    pisa_status = pisa.CreatePDF(BytesIO(html_content.encode("utf-8")), dest=response)
    if pisa_status.err:
        return HttpResponse("PDF yaratishda xatolik yuz berdi", status=500)

    return response


def StatisticsDownload(request, date):
    start = datetime(2024, 10, 1)
    month_name = [
        "Yanvar",
        "Fevral",
        "Mart",
        "Aprel",
        "May",
        "Iyun",
        "Iyul",
        "Avgust",
        "Sentabr",
        "Oktabr",
        "Noyabr",
        "Dekabr",
    ]
    action = str(date).split(":::")
    start_date = action[0]
    end_date = action[1]

    contracts = Client.objects.filter(created__date__range=(start_date, end_date))
    contract = 0
    dcontract = 0
    for v in contracts:
        if v.status in ["Rasmiylashtirilgan", "Tugallangan"]:
            contract += 1
        if v.status == "Bekor qilingan":
            dcontract += 1

    clients = ClientInformation.objects.filter(
        created__date__range=(start_date, end_date)
    )
    rasrochka = Rasrochka.objects.filter(date__date__range=(start_date, end_date))
    s = 0
    for i in rasrochka:
        s += i.amount

    # HTML tarkibini tayyorlash
    html_content = """
    <html>
        <head>
            <style>
            .title{
                font-size: 22px;
               text-align: center;
               border-bottom: 1px solid black;
                      font-family: "Times New Roman", Times, serif;
            }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    border: 1px solid black;
                    padding: 5px;
                    text-align: center;
                    font-size: 15px;
                      font-family: "Times New Roman", Times, serif;
                }
                .m {
                    border: 1px solid black;
                    font-weight: bold;
                }
                th {
                    background-color: #f2f2f2;
                }
                .n{
                    width: 20%
                }
            </style>
        </head>
        <body>
            <h2 class="title">Oylik tushum hisoboti.
    """
    html_content += f"""
     {month_name[int(str(start_date).split("-")[1]) - 1]}, {str(start_date).split("-")[0]} - yil</h2>
            
            
            <table>
                <tbody>"""
    html_content += f"""
                    <tr>
                        <td class="m">Barcha mijozlar</td>
                        <td>{len(clients)}</td>
                    </tr>
                    <tr>
                        <td class="m">Shartnomalar</td>
                        <td>             
                            <table>
                                <tbody>
                                    <tr> 
                                        <td class="m">Barchasi</td>
                                        <td>{len(contracts)}</td>
                                    </tr>
                                    <tr> 
                                        <td class="m">Rasmiylashtirilgan</td>
                                        <td>{contract}</td>
                                    </tr>
                                    <tr> 
                                        <td class="m">Bekor qilingan</td>
                                        <td>{dcontract}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </td>
                    </tr>

                    """

    html_content += """
                </tbody>
            </table>
        </body>
    </html>
    """

    # PDFni yaratish
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Oylik tushum. {month_name[int(str(start_date).split("-")[1]) - 1]}, {str(start_date).split("-")[0]}.pdf"'
    )

    pisa_status = pisa.CreatePDF(BytesIO(html_content.encode("utf-8")), dest=response)
    if pisa_status.err:
        return redirect("statistika")

    return response


def number_to_words_uz(number):
    units = [
        "",
        "бир",
        "икки",
        "уч",
        "тўрт",
        "беш",
        "олти",
        "тўққиз",
        "саккиз",
        "тўққиз",
    ]
    tens = [
        "",
        "ўн",
        "йигирма",
        "ўттиз",
        "қирқ",
        "эллик",
        "олтимиш",
        "жетмиш",
        "саксон",
        "тўқсон",
    ]
    scales = ["", "миң", "миллион", "миллиард", "трилион", "квадрилион"]

    def integer_to_words(num):
        if num == 0:
            return "нол"
        words = []
        num_str = str(num)[::-1]
        groups = [num_str[i : i + 3] for i in range(0, len(num_str), 3)]

        for idx, group in enumerate(groups):
            group_word = []
            hundreds, remainder = divmod(int(group[::-1]), 100)
            tens_unit = remainder % 10
            tens_place = remainder // 10

            if hundreds > 0:
                group_word.append(units[hundreds] + " юз")

            if tens_place > 0:
                group_word.append(tens[tens_place])

            if tens_unit > 0:
                group_word.append(units[tens_unit])

            if group_word and scales[idx]:
                group_word.append(scales[idx])

            words = group_word + words

        return " ".join(words)

    integer_part = int(number)
    fractional_part = round(number % 1, 2)
    fractional_str = str(fractional_part)[2:] if fractional_part > 0 else None

    result = integer_to_words(integer_part)
    if fractional_str:
        result += f" бутун {integer_to_words(int(fractional_str))}"

    return result


def qisqartirish(full_name):
    parts = full_name.split()
    if len(parts) == 3 or len(parts) == 4:
        return f"{parts[0]} {parts[1][0].upper()}. {parts[2][0].upper()}"
    elif len(parts) == 2:
        return f"{parts[0]} {parts[1][0].upper()}."
    elif len(parts) == 1:
        return parts[0]
    return full_name


def ContractCreatePDF(request, id):
    contract = get_object_or_404(Client, pk=id)
    company = get_object_or_404(Company, pk=contract.home.building.city.company.pk)
    
    month_name = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]
    month = month_name[contract.created.date().month - 1]
    
    price = contract.home.home.price * contract.home.home.field
    try:
        foiz = (contract.payment / price) / 100
    except:
        foiz = 0

    html_content = render_to_string(
        "shart.html",
        {
            "pk": id,
            "contract": contract,
            "month": month, 
            "price": price,
            "price_text": number_to_words_uz(price),
            "pay_text": number_to_words_uz(contract.payment),
            "foiz": '%.2f' % foiz,
            "company": company,
            "dr": qisqartirish(company.direktor),
        },
    )

    font_config = FontConfiguration()
    pdf = HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(font_config=font_config)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="shartnoma-{id}.pdf"'
    return response


def LoginPage(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            return render(
                request=request,
                template_name="login.html",
                context={
                    "error": "Login yoki parol noto'g'ri",
                    "userr": username,
                    "pass": password,
                },
            )
    return render(request=request, template_name="login.html")


def LogoutPage(request):
    logout(request)
    return redirect("login")