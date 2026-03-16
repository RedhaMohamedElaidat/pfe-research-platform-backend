# team/serializers.py
from rest_framework import serializers
from team.models import Team


class TeamMemberSerializer(serializers.Serializer):
    """Serializer léger pour afficher les membres d'une équipe."""
    user_id        = serializers.IntegerField(source='user_id')
    username       = serializers.CharField()
    full_name      = serializers.SerializerMethodField()
    h_index        = serializers.SerializerMethodField()
    research_field = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_h_index(self, obj):
        try:
            return obj.researcher_profile.h_index
        except Exception:
            return None

    def get_research_field(self, obj):
        try:
            return obj.researcher_profile.research_field
        except Exception:
            return None


class TeamSerializer(serializers.ModelSerializer):
    laboratory_name = serializers.CharField(source='laboratory.name', read_only=True)
    current_leader  = serializers.SerializerMethodField()
    member_count    = serializers.SerializerMethodField()

    class Meta:
        model  = Team
        fields = [
            'ID', 'name', 'description',
            'laboratory', 'laboratory_name',
            'current_leader', 'member_count',
        ]

    def get_current_leader(self, obj):
        leader = obj.current_leader
        if leader:
            return {
                'user_id':  leader.user_id,
                'username': leader.username,
                'name':     leader.get_full_name(),
            }
        return None

    def get_member_count(self, obj):
        return obj.members.count()


class TeamDetailSerializer(TeamSerializer):
    """Serializer enrichi avec la liste complète des membres."""
    members = serializers.SerializerMethodField()

    class Meta(TeamSerializer.Meta):
        fields = TeamSerializer.Meta.fields + ['members']

    def get_members(self, obj):
        return TeamMemberSerializer(obj.members.all(), many=True).data


class TeamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Team
        fields = ['name', 'description', 'laboratory']

    def validate_name(self, value):
        value = value.strip()
        if Team.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Une équipe avec ce nom existe déjà.")
        return value