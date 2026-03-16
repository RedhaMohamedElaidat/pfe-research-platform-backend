from django.db import models

from publication.models import Publication


class Laboratory(models.Model):
    ID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    institution = models.ForeignKey('institution.Institution', on_delete=models.SET_NULL, null=True, blank=True, related_name='laboratories')
    class Meta:
        db_table = 'laboratory'
        ordering = ['name']
    def __str__(self):
        return self.name
    
    @property
    def current_manager(self):
        manager = self.lab_managers.filter(end_date__isnull=True).first()
        return manager.user if manager else None
    
    def get_productivity_score(self) -> float:
        from django.utils import timezone
        from django.db.models import Avg
        current_year = timezone.now().year
        pubs = Publication.objects.filter(
            coauthors__author__researcher_profile__isnull=False,
            coauthors__author__team_leader_profile__team__laboratory=self,
            publication_year=current_year
        )
        if not pubs.exists():
            return 0.0
        avg_citations = pubs.aggregate(avg=Avg('citation_count'))['avg'] or 0
        return round(pubs.count() * (1 + avg_citations / 100), 2)
