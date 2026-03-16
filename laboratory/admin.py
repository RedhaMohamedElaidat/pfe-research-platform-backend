from laboratory.models import Laboratory
from django.contrib import admin

@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
        list_display  = ['ID', 'name', 'institution', 'website',
                        'get_current_manager', 'get_team_count']
        search_fields = ['name', 'description']
        list_filter   = ['institution']
        ordering      = ['name']
        list_per_page = 25

        def get_current_manager(self, obj):
            manager = obj.current_manager
            return manager.get_full_name() if manager else '—'
        get_current_manager.short_description = 'Directeur'

        def get_team_count(self, obj):
            return obj.teams.count()
        get_team_count.short_description = 'Équipes'

