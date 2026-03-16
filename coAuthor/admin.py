# coAuthor/admin.py
from django.contrib import admin
from coAuthor.models import CoAuthor


@admin.register(CoAuthor)
class CoAuthorAdmin(admin.ModelAdmin):
    list_display  = [
        'ID', 'author_name', 'publication_short',
        'get_contribution_type_display', 'author_order',
        'affiliation_at_time',
    ]
    search_fields = [
        'author__username',
        'author__first_name',
        'author__last_name',
        'publication__title',
    ]
    list_filter   = ['contribution_type']
    ordering      = ['publication', 'author_order']
    list_per_page = 25

    def author_name(self, obj):
        return obj.author.get_full_name()
    author_name.short_description = 'Auteur'

    def publication_short(self, obj):
        return obj.publication.title[:50]
    publication_short.short_description = 'Publication'