# laboratory/views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from laboratory.models import Laboratory
from laboratory.serializers import (
    LaboratorySerializer, LaboratoryDetailSerializer, LaboratoryCreateSerializer
)


class LaboratoryViewSet(viewsets.ModelViewSet):
    queryset           = Laboratory.objects.select_related('institution').prefetch_related('teams')
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['institution']
    search_fields      = ['name', 'description']
    ordering_fields    = ['name']
    ordering           = ['name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LaboratoryDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return LaboratoryCreateSerializer
        return LaboratorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """GET /api/laboratories/{id}/stats/"""
        from django.db.models import Avg, Sum, Max
        from users.models import Researcher
        from publication.models import Publication

        lab         = self.get_object()
        researchers = Researcher.objects.filter(user__teams__laboratory=lab)
        pubs        = Publication.objects.filter(
            coauthors__author__teams__laboratory=lab,
            is_validated=True
        ).distinct()
        agg = researchers.aggregate(avg_h=Avg('h_index'), max_h=Max('h_index'))

        return Response({
            'name':                lab.name,
            'team_count':          lab.teams.count(),
            'researcher_count':    researchers.count(),
            'avg_h_index':         round(agg['avg_h'] or 0, 2),
            'max_h_index':         agg['max_h'] or 0,
            'total_publications':  pubs.count(),
            'total_citations':     pubs.aggregate(t=Sum('citation_count'))['t'] or 0,
            'productivity_score':  lab.get_productivity_score(),
        })

    @action(detail=True, methods=['get'])
    def teams(self, request, pk=None):
        """GET /api/laboratories/{id}/teams/"""
        from team.serializers import TeamSerializer
        lab = self.get_object()
        return Response(TeamSerializer(lab.teams.all(), many=True).data)

    @action(detail=True, methods=['get'])
    def top_researchers(self, request, pk=None):
        """GET /api/laboratories/{id}/top_researchers/?n=10"""
        from users.models import Researcher
        from users.serializers import ResearcherSerializer
        n   = int(request.query_params.get('n', 10))
        lab = self.get_object()
        researchers = (
            Researcher.objects
            .filter(user__teams__laboratory=lab)
            .order_by('-h_index')
            .select_related('user')[:n]
        )
        return Response(ResearcherSerializer(researchers, many=True).data)

    @action(detail=True, methods=['get'])
    def publications(self, request, pk=None):
        """GET /api/laboratories/{id}/publications/"""
        from publication.models import Publication
        from publication.serializers import PublicationSerializer
        lab  = self.get_object()
        pubs = Publication.objects.filter(
            coauthors__author__teams__laboratory=lab,
            is_validated=True
        ).distinct().order_by('-publication_year')
        return Response(PublicationSerializer(pubs, many=True).data)