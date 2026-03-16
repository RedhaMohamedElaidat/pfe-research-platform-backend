# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User, Admin, Researcher, LabManager, TeamLeader


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ['user_id', 'username', 'email', 'first_name',
                      'last_name', 'is_active', 'is_staff', 'created_at']
    search_fields  = ['username', 'email', 'first_name', 'last_name']
    list_filter    = ['is_active', 'is_staff']
    ordering       = ['-created_at']
    list_per_page  = 25
    fieldsets      = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display  = ['user', 'role']
    list_filter   = ['role']
    search_fields = ['user__username', 'user__email']


@admin.register(Researcher)
class ResearcherAdmin(admin.ModelAdmin):
    list_display  = ['user', 'orcid', 'research_field', 'h_index']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'orcid']
    list_filter   = ['research_field']
    ordering      = ['-h_index']
    list_per_page = 25


@admin.register(LabManager)
class LabManagerAdmin(admin.ModelAdmin):
    list_display  = ['user', 'laboratory', 'start_date', 'end_date']
    search_fields = ['user__username', 'laboratory__name']
    list_filter   = ['laboratory']


@admin.register(TeamLeader)
class TeamLeaderAdmin(admin.ModelAdmin):
    list_display  = ['user', 'team', 'start_date', 'end_date']
    search_fields = ['user__username', 'team__name']
    list_filter   = ['team']