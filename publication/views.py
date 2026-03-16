# publication/views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from publication.models import Publication
from publication.serializers import (
    PublicationSerializer, PublicationCreateSerializer,
    PublicationListSerializer, PublicationValidateSerializer
)


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = (
        Publication.objects
        .select_related('journal', 'institution')
        .prefetch_related('keywords', 'coauthors__author')
    )
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['type', 'publication_year', 'is_validated', 'institution', 'journal']
    search_fields      = ['title', 'abstract', 'doi', 'keywords__label']
    ordering_fields    = ['publication_year', 'citation_count', 'altmetric_score']
    ordering           = ['-publication_year']

    def get_serializer_class(self):
        if self.action == 'list':
            return PublicationListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return PublicationCreateSerializer
        return PublicationSerializer

    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    # ── Validation ────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def validate(self, request, pk=None):
        """POST /api/publications/{id}/validate/"""
        pub = self.get_object()
        pub.validate()
        return Response({'detail': f'Publication "{pub.title[:50]}" validée.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """POST /api/publications/{id}/reject/"""
        pub = self.get_object()
        pub.is_validated = False
        pub.save(update_fields=['is_validated'])
        return Response({'detail': f'Publication "{pub.title[:50]}" rejetée.'})

    # ── Indicateurs ───────────────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """GET /api/publications/{id}/stats/"""
        pub = self.get_object()
        return Response({
            'citation_count':  pub.get_citation_count(),
            'impact_factor':   pub.get_impact_factor(),
            'altmetric_score': pub.get_altmetric_score(),
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def refresh_citations(self, request, pk=None):
        """POST /api/publications/{id}/refresh_citations/"""
        pub = self.get_object()
        pub.refresh_citation_count()
        return Response({'citation_count': pub.citation_count})

    # ── Listes filtrées ───────────────────────────────────────────────────

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """GET /api/publications/pending/ — publications en attente de validation"""
        qs = self.get_queryset().filter(is_validated=False)
        return Response(PublicationListSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def top_cited(self, request):
        """GET /api/publications/top_cited/?n=10&year=2024"""
        n    = int(request.query_params.get('n', 10))
        year = request.query_params.get('year')
        qs   = self.get_queryset().filter(is_validated=True).order_by('-citation_count')
        if year:
            qs = qs.filter(publication_year=year)
        return Response(PublicationListSerializer(qs[:n], many=True).data)

    # ── Co-auteurs ────────────────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def coauthors(self, request, pk=None):
        """GET /api/publications/{id}/coauthors/"""
        from coAuthor.models import CoAuthor
        from coAuthor.serializers import CoAuthorSerializer
        pub      = self.get_object()
        coauthors = CoAuthor.objects.filter(publication=pub).select_related('author')
        return Response(CoAuthorSerializer(coauthors, many=True).data)

    # ── Citations ─────────────────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def citations(self, request, pk=None):
        """GET /api/publications/{id}/citations/"""
        from citation.models import Citation
        from citation.serializers import CitationSerializer
        pub      = self.get_object()
        received = Citation.objects.filter(cited_publication=pub).select_related('citing_publication')
        return Response(CitationSerializer(received, many=True).data)