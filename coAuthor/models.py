from django.db import models
from publication.models import *
from users.models import *
# Create your models here.
class CoAuthor(models.Model):
    ID = models.AutoField(primary_key=True)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='coauthors')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coauthored_publications')
    contribution_type = models.IntegerField(choices=[(1, 'First Author'), (2, 'Second Author'), (3, 'Third Author'), (4, 'Corresponding Author'), (5, 'Other')], default=1)
    author_order = models.IntegerField(default=1)
    affiliation_at_time = models.CharField(max_length=255, blank=True)  # Affiliation au moment de la publication

    class Meta:
        db_table = 'coauthors'
        verbose_name = 'CoAuthor'
        verbose_name_plural = 'CoAuthors'
        unique_together = ('publication', 'author')
    def __str__(self):
        return f"{self.author.get_full_name()} - {self.publication.title[:30]} (Contribution: {self.get_contribution_type_display()})"
    