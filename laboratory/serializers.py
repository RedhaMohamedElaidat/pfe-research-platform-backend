# laboratory/serializers.py
from rest_framework import serializers
from laboratory.models import Laboratory


class LaboratorySerializer(serializers.ModelSerializer):
    institution_name  = serializers.CharField(source='institution.name',      read_only=True)
    current_manager   = serializers.SerializerMethodField()
    team_count        = serializers.SerializerMethodField()

    class Meta:
        model  = Laboratory
        fields = [
            'ID', 'name', 'description', 'website',
            'institution', 'institution_name',
            'current_manager', 'team_count',
        ]

    def get_current_manager(self, obj):
        manager = obj.current_manager
        if manager:
            return {
                'user_id':  manager.user_id,
                'username': manager.username,
                'name':     manager.get_full_name(),
            }
        return None

    def get_team_count(self, obj):
        return obj.teams.count()


class LaboratoryDetailSerializer(LaboratorySerializer):
    """Serializer enrichi avec teams et indicateurs."""
    teams               = serializers.SerializerMethodField()
    productivity_score  = serializers.SerializerMethodField()

    class Meta(LaboratorySerializer.Meta):
        fields = LaboratorySerializer.Meta.fields + ['teams', 'productivity_score']

    def get_teams(self, obj):
        from team.serializers import TeamSerializer
        return TeamSerializer(obj.teams.all(), many=True).data

    def get_productivity_score(self, obj):
        return obj.get_productivity_score()


class LaboratoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Laboratory
        fields = ['name', 'description', 'website', 'institution']

    def validate_name(self, value):
        value = value.strip()
        if Laboratory.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Un laboratoire avec ce nom existe déjà.")
        return value