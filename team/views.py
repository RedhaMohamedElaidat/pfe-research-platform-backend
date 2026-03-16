# team/views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from team.models import Team
from team.serializers import (
    TeamSerializer, TeamDetailSerializer,
    TeamCreateSerializer, TeamMemberSerializer
)


class TeamViewSet(viewsets.ModelViewSet):
    queryset           = Team.objects.select_related('laboratory').prefetch_related('members')
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['laboratory']
    search_fields      = ['name', 'description']
    ordering_fields    = ['name']
    ordering           = ['name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TeamDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return TeamCreateSerializer
        return TeamSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    # ── Membres ───────────────────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """GET /api/teams/{id}/members/"""
        team = self.get_object()
        return Response(TeamMemberSerializer(team.members.all(), many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def add_member(self, request, pk=None):
        """POST /api/teams/{id}/add_member/ — body: {user_id: X}"""
        team    = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id requis.'}, status=status.HTTP_400_BAD_REQUEST)
        from users.models import User
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        team.members.add(user)
        return Response({'detail': f'{user.get_full_name()} ajouté à {team.name}.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def remove_member(self, request, pk=None):
        """POST /api/teams/{id}/remove_member/ — body: {user_id: X}"""
        team    = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id requis.'}, status=status.HTTP_400_BAD_REQUEST)
        from users.models import User
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        team.members.remove(user)
        return Response({'detail': f'{user.get_full_name()} retiré de {team.name}.'})

    # ── Stats ─────────────────────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """GET /api/teams/{id}/stats/"""
        from django.db.models import Avg, Sum
        from users.models import Researcher
        from publication.models import Publication

        team        = self.get_object()
        researchers = Researcher.objects.filter(user__teams=team)
        pubs        = Publication.objects.filter(
            coauthors__author__teams=team,
            is_validated=True
        ).distinct()
        agg = researchers.aggregate(avg_h=Avg('h_index'))

        return Response({
            'team_name':      team.name,
            'member_count':   team.members.count(),
            'avg_h_index':    round(agg['avg_h'] or 0, 2),
            'total_pubs':     pubs.count(),
            'total_citations': pubs.aggregate(t=Sum('citation_count'))['t'] or 0,
            'leader':         (
                team.current_leader.get_full_name()
                if team.current_leader else None
            ),
        })