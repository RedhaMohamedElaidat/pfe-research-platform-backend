# coAuthor/views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from coAuthor.models import CoAuthor
from coAuthor.serializers import (
    CoAuthorSerializer, CoAuthorCreateSerializer, CoAuthorBulkSerializer
)


class CoAuthorViewSet(viewsets.ModelViewSet):
    queryset = CoAuthor.objects.select_related(
        'author__researcher_profile',
        'publication'
    )
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['publication', 'author', 'contribution_type']
    ordering_fields    = ['author_order']
    ordering           = ['author_order']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CoAuthorCreateSerializer
        return CoAuthorSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_add']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    # ── Ajout groupé ──────────────────────────────────────────────────────

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_add(self, request):
        """
        POST /api/coauthors/bulk_add/
        Ajoute plusieurs co-auteurs pour une même publication en une requête.
        body: {
            publication_id: 1,
            authors: [
                {author: 2, contribution_type: 1, author_order: 1, affiliation_at_time: "CERIST"},
                {author: 3, contribution_type: 2, author_order: 2, affiliation_at_time: "USTHB"}
            ]
        }
        """
        serializer = CoAuthorBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pub_id  = serializer.validated_data['publication_id']
        authors = serializer.validated_data['authors']
        created = []

        for author_data in authors:
            ca, created_flag = CoAuthor.objects.get_or_create(
                publication_id=pub_id,
                author=author_data['author'],
                defaults={
                    'contribution_type':  author_data.get('contribution_type', 5),
                    'author_order':       author_data.get('author_order', 1),
                    'affiliation_at_time': author_data.get('affiliation_at_time', ''),
                }
            )
            if created_flag:
                created.append(ca)

        return Response(
            CoAuthorSerializer(created, many=True).data,
            status=status.HTTP_201_CREATED
        )

    # ── Par publication ───────────────────────────────────────────────────

    @action(detail=False, methods=['get'])
    def by_publication(self, request):
        """
        GET /api/coauthors/by_publication/?id=X
        Retourne tous les co-auteurs d'une publication triés par order.
        """
        pub_id = request.query_params.get('id')
        if not pub_id:
            return Response(
                {'error': 'Paramètre id requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        qs = CoAuthor.objects.filter(
            publication_id=pub_id
        ).select_related('author__researcher_profile').order_by('author_order')
        return Response(CoAuthorSerializer(qs, many=True).data)

    # ── Par auteur ────────────────────────────────────────────────────────

    @action(detail=False, methods=['get'])
    def by_author(self, request):
        """
        GET /api/coauthors/by_author/?id=X
        Retourne toutes les collaborations d'un auteur.
        """
        author_id = request.query_params.get('id')
        if not author_id:
            return Response(
                {'error': 'Paramètre id requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        qs = CoAuthor.objects.filter(
            author_id=author_id
        ).select_related('publication').order_by('-publication__publication_year')
        return Response(CoAuthorSerializer(qs, many=True).data)