"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main.views import *

urlpatterns = [
    path("", HomePage, name="home"),
    
    path("login/", LoginPage, name="login"),
    path("loguot/", LogoutPage, name="loguot"),
    
    path("company/", CompanyPage, name="company"),
    path("company/create/", CompanyCreate, name="company-create"),
    path("company/delete/<int:id>/", CompanyDelete, name="company-delete"),
    path("company/edit/<int:id>/", CompanyEdit, name="company-edit"),
    
    path("city/", CityPage, name="city"),
    path("city/create/", CityCreate, name="city-create"),
    path("city/delete/<int:id>/", CityDelete, name="city-delete"),
    path("city/edit/<int:id>/", CityEdit, name="city-edit"),
    
    path("building/", BuildingPage, name="building"),
    path("building/create/", BuildingCreate, name="building-create"),
    path("building/delete/<int:id>/", BuildingDelete, name="building-delete"),
    path("building/edit/<int:id>/", BuildingEdit, name="building-edit"),
    path("building/information/", BuildingInformation, name="building-info"),
    
    
    path("home/", HomePagee, name="homee"),
    path("home/create/", HomeCreate, name="home-create"),
    path("home/delete/<int:id>/", HomeDelete, name="home-delete"),
    path("home/edit/<int:id>/", HomeEdit, name="home-edit"),
    path("home/upload/", HomeUpload, name="home-upload"),
    path("home/download/", HomeDownload, name="home-download"),

    path("client/", ClientPage, name="client"),
    path("client/create/", ClientCreate, name="client-create"),
    path("client/delete/<int:id>/", ClientDelete, name="client-delete"),
    path("client/edit/<int:id>/", ClientEdit, name="client-edit"),

    path("contract/", ContractPage, name="contract"),
    path("contract/create/", ContractCreate, name="contract-create"),
    path("contract/delete/<int:id>/", ContractDelete, name="contract-delete"),
    path("contract/edit/<int:id>/", ContractEdit, name="contract-edit"),
    path("contract/<int:id>/", ContractCreatePDF, name="contract-pdf"),
    path("contract/<int:id>/list/", JadvalPage, name="jadval"),
    path("contract/<int:id>/list/download/", JadvalDownload, name="jadval-download"),
    
    # path("debtor/", DebtorPage, name="debtor"),

    path("statistics/", Statistika, name="statistika"),
    path("statistics/download/", StatisticsDownloadAll, name="statistika-all"),
    path("statistics/download/<str:date>/", StatisticsDownload, name="statistika-date"),
    
    # path('html_to_pdf/', html_to_pdf, name='html_to_pdf'),
]