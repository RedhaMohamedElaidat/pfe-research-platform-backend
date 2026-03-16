# institution/serializers.py
from rest_framework import serializers
from institution.models import Country, Wilaya, Commune, Ville, Institution


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Country
        fields = ['ID', 'name']


class WilayaSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)

    class Meta:
        model  = Wilaya
        fields = ['ID', 'name', 'country', 'country_name']


class CommuneSerializer(serializers.ModelSerializer):
    wilaya_name = serializers.CharField(source='wilaya.name', read_only=True)

    class Meta:
        model  = Commune
        fields = ['ID', 'name', 'wilaya', 'wilaya_name']


class VilleSerializer(serializers.ModelSerializer):
    commune_name = serializers.CharField(source='commune.name', read_only=True)

    class Meta:
        model  = Ville
        fields = ['ID', 'name', 'commune', 'commune_name']


class InstitutionSerializer(serializers.ModelSerializer):
    ville_name   = serializers.CharField(source='ville.name',            read_only=True)
    commune_name = serializers.CharField(source='ville.commune.name',    read_only=True)
    wilaya_name  = serializers.CharField(source='ville.commune.wilaya.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display',      read_only=True)

    class Meta:
        model  = Institution
        fields = [
            'ID', 'name', 'description', 'type', 'type_display',
            'website', 'ville', 'ville_name', 'commune_name', 'wilaya_name',
        ]


class InstitutionDetailSerializer(InstitutionSerializer):
    """Serializer enrichi avec les indicateurs calculés."""
    total_publications = serializers.SerializerMethodField()
    average_h_index    = serializers.SerializerMethodField()
    top_researchers    = serializers.SerializerMethodField()

    class Meta(InstitutionSerializer.Meta):
        fields = InstitutionSerializer.Meta.fields + [
            'total_publications', 'average_h_index', 'top_researchers'
        ]

    def get_total_publications(self, obj) -> int:
        return obj.get_total_publications()

    def get_average_h_index(self, obj) -> float:
        return obj.get_average_h_index()

    def get_top_researchers(self, obj) -> list:
        researchers = obj.get_top_researchers(limit=5)
        return [
            {
                'id':        u.user_id,
                'name':      u.get_full_name(),
                'h_index':   getattr(getattr(u, 'researcher_profile', None), 'h_index', 0),
            }
            for u in researchers
        ]