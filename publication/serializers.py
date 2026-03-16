# publication/serializers.py
from rest_framework import serializers
from publication.models import Publication, PublicationType
from journal.serializers import JournalSerializer
from keywords.serializers import KeywordSerializer


class PublicationSerializer(serializers.ModelSerializer):
    journal_detail   = JournalSerializer(source='journal', read_only=True)
    keywords_detail  = KeywordSerializer(source='keywords', many=True, read_only=True)
    type_display     = serializers.CharField(source='get_type_display', read_only=True)
    impact_factor    = serializers.SerializerMethodField()

    class Meta:
        model  = Publication
        fields = [
            'id', 'title', 'abstract', 'publication_year',
            'doi', 'type', 'type_display',
            'institution', 'journal', 'journal_detail',
            'keywords', 'keywords_detail',
            'citation_count', 'altmetric_score',
            'is_validated', 'impact_factor',
        ]
        read_only_fields = ['id', 'citation_count']

    def get_impact_factor(self, obj) -> float:
        return obj.get_impact_factor()


class PublicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Publication
        fields = [
            'title', 'abstract', 'publication_year',
            'doi', 'type', 'institution',
            'journal', 'keywords', 'altmetric_score',
        ]

    def validate_publication_year(self, value):
        from django.utils import timezone
        current_year = timezone.now().year
        if value and (value < 1900 or value > current_year):
            raise serializers.ValidationError(
                f"L'année doit être entre 1900 et {current_year}."
            )
        return value

    def validate_doi(self, value):
        if value and not value.startswith('10.'):
            raise serializers.ValidationError(
                "DOI invalide — doit commencer par '10.'"
            )
        return value


class PublicationListSerializer(serializers.ModelSerializer):
    """Serializer léger pour les listes — sans abstract ni détails."""
    journal_name = serializers.CharField(source='journal.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model  = Publication
        fields = [
            'id', 'title', 'publication_year', 'type', 'type_display',
            'doi', 'citation_count', 'is_validated',
            'journal_name', 'altmetric_score',
        ]


class PublicationValidateSerializer(serializers.ModelSerializer):
    """Utilisé par l'admin pour valider ou rejeter une publication."""
    class Meta:
        model  = Publication
        fields = ['is_validated']