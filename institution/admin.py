# institution/admin.py
from django.contrib import admin
from institution.models import Country, Wilaya, Commune, Ville, Institution


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display  = ['ID', 'name']
    search_fields = ['name']
    ordering      = ['name']


@admin.register(Wilaya)
class WilayaAdmin(admin.ModelAdmin):
    list_display  = ['ID', 'name', 'country']
    search_fields = ['name']
    list_filter   = ['country']
    ordering      = ['name']


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display  = ['ID', 'name', 'wilaya']
    search_fields = ['name']
    list_filter   = ['wilaya']
    ordering      = ['name']


@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display  = ['ID', 'name', 'commune']
    search_fields = ['name']
    list_filter   = ['commune']
    ordering      = ['name']


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display   = ['ID', 'name', 'type', 'ville', 'website']
    search_fields  = ['name', 'description']
    list_filter    = ['type']
    ordering       = ['name']
    list_per_page  = 25