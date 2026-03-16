from django.db import models


class TypeInstitution(models.TextChoices):
    UNIVERSITY        = 'University',        'Université'
    RESEARCH_CENTER   = 'Research_Center',   'Centre de Recherche'
    UNIVERSITY_CENTER = 'University_Center', 'Centre Universitaire'
    ECOLE             = 'Ecole',             'Ecole'


class Country(models.Model):
    ID   = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'country'
        ordering = ['name']

    def __str__(self):
        return self.name


class Wilaya(models.Model):                          # ✅ PascalCase
    ID      = models.AutoField(primary_key=True)
    name    = models.CharField(max_length=200, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='wilayas')

    class Meta:
        db_table = 'wilaya'
        ordering = ['name']

    def __str__(self):
        return self.name


class Commune(models.Model):
    ID     = models.AutoField(primary_key=True)
    name   = models.CharField(max_length=200, unique=True)
    wilaya = models.ForeignKey(Wilaya, on_delete=models.CASCADE, related_name='communes')  # ✅ Commune → Wilaya

    class Meta:
        db_table = 'commune'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ville(models.Model):
    ID      = models.AutoField(primary_key=True)
    name    = models.CharField(max_length=200, unique=True)
    commune = models.ForeignKey(Commune, on_delete=models.CASCADE, related_name='villes')  # ✅ Ville → Commune

    class Meta:
        db_table = 'ville'
        ordering = ['name']

    def __str__(self):
        return self.name


class Institution(models.Model):
    ID          = models.AutoField(primary_key=True)
    name        = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    type        = models.CharField(max_length=20, choices=TypeInstitution.choices, default=TypeInstitution.UNIVERSITY)
    website     = models.URLField(blank=True)
    ville       = models.ForeignKey(Ville, on_delete=models.SET_NULL, null=True, blank=True, related_name='institutions')

    # ⚠️ publications M2M supprimé → déjà géré via Publication.institution (FK)
    # ⚠️ Laboratories M2M supprimé → à ajouter comme FK dans laboratory/models.py

    class Meta:
        db_table = 'institution'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_total_publications(self) -> int:
        return self.publications.count()

    def get_average_h_index(self) -> float:
        values = list(
            self.publications
                .values_list('coauthors__author__researcher_profile__h_index', flat=True)
        )
        values = [h for h in values if h is not None]
        return round(sum(values) / len(values), 2) if values else 0.0

    def get_top_researchers(self, limit: int = 5):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return (
            User.objects
                .filter(coauthored_publications__publication__institution=self)
                .distinct()
                .order_by('-researcher_profile__h_index')[:limit]
        )
