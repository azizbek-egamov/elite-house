from django.contrib import admin
from main.models import * 

# Register your models here

admin.site.register(City)
admin.site.register(Building)
admin.site.register(Home)
admin.site.register(HomeInformation)
admin.site.register(ClientInformation)
admin.site.register(Company)
admin.site.register(Client)
admin.site.register(Rasrochka)
# class AdminClient(admin.ModelAdmin):
#     list_display = ["full_name", "telefon", "city", "building", "home", "passport", "term", "payment", "residual", "oylik_tolov", "count_month", "status"]
