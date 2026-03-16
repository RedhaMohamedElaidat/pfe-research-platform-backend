# coAuthor/serializers.py
from rest_framework import serializers
from coAuthor.models import CoAuthor


class CoAuthorSerializer(serializers.ModelSerializer):
    author_name          = serializers.CharField(
        source='author.get_full_name', read_only=True
    )
    author_username      = serializers.CharField(
        source='author.username', read_only=True
    )
    publication_title    = serializers.CharField(
        source='publication.title', read_only=True
    )
    contribution_display = serializers.CharField(
        source='get_contribution_type_display', read_only=True
    )
    h_index              = serializers.SerializerMethodField()

    class Meta:
        model  = CoAuthor
        fields = [
            'ID',
            'publication', 'publication_title',
            'author', 'author_name', 'author_username',
            'contribution_type', 'contribution_display',
            'author_order', 'affiliation_at_time',
            'h_index',
        ]
        read_only_fields = ['ID']

    def get_h_index(self, obj) -> int:
        try:
            return obj.author.researcher_profile.h_index
        except Exception:
            return 0


class CoAuthorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CoAuthor
        fields = [
            'publication', 'author',
            'contribution_type', 'author_order',
            'affiliation_at_time',
        ]

    def validate(self, attrs):
        # Doublon publication + auteur
        if CoAuthor.objects.filter(
            publication=attrs['publication'],
            author=attrs['author']
        ).exists():
            raise serializers.ValidationError(
                "Cet auteur est déjà enregistré pour cette publication."
            )
        return attrs

    def validate_author_order(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "L'ordre de l'auteur doit être supérieur ou égal à 1."
            )
        return value


class CoAuthorBulkSerializer(serializers.Serializer):
    """
    Permet d'ajouter plusieurs co-auteurs en une seule requête.
    body: { publication_id: X, authors: [{author, contribution_type, author_order, affiliation_at_time}] }
    """
    publication_id = serializers.IntegerField()
    authors        = CoAuthorCreateSerializer(many=True)

    def validate_publication_id(self, value):
        from publication.models import Publication
        if not Publication.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Publication introuvable.")
        return value