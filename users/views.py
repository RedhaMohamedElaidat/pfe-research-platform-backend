# users/views.py
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from users.models import User, Researcher, Admin, LabManager, TeamLeader
from rest_framework import filters
from users.serializers import (
    UserSerializer, RegisterSerializer, ChangePasswordSerializer,
    ResearcherSerializer, ResearcherUpdateSerializer,
    AdminSerializer, LabManagerSerializer, TeamLeaderSerializer
)

# IMPORTATION DU PIPELINE OPENALEX
from data_pipeline.openalex_verify import verify_orcid
from data_pipeline.openalex_researcher_sync import sync_researcher
import logging
logger = logging.getLogger(__name__)

# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    serializer_class   = RegisterSerializer
    permission_classes = [AllowAny]


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class   = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Mot de passe mis à jour avec succès.'})


# ─── User ─────────────────────────────────────────────────────────────────────

class UserViewSet(viewsets.ModelViewSet):
    queryset           = User.objects.all()
    serializer_class   = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['username', 'email', 'first_name', 'last_name']
    ordering_fields    = ['username', 'created_at']
    ordering           = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'destroy', 'update', 'partial_update']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """GET /api/users/me/ — profil de l'utilisateur connecté"""
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """PATCH /api/users/update_profile/"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def activate(self, request, pk=None):
        """POST /api/users/{id}/activate/"""
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({'detail': f'{user.username} activé.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def deactivate(self, request, pk=None):
        """POST /api/users/{id}/deactivate/"""
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({'detail': f'{user.username} désactivé.'})


# ─── Researcher ───────────────────────────────────────────────────────────────

class ResearcherViewSet(viewsets.ModelViewSet):
    queryset           = Researcher.objects.select_related('user')
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['research_field']
    search_fields      = ['user__username', 'user__first_name', 'user__last_name', 'orcid']
    ordering_fields    = ['h_index']
    ordering           = ['-h_index']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'update_profile', 'save_orcid']:
            return ResearcherUpdateSerializer
        return ResearcherSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """GET /api/researchers/{id}/stats/"""
        researcher = self.get_object()
        return Response({
            'h_index':         researcher.h_index,
            'pub_count':       researcher.user.coauthored_publications.count(),
            'orcid':           researcher.orcid,
            'research_field':  researcher.research_field,
            'total_citations': sum(
                ca.publication.citation_count
                for ca in researcher.user.coauthored_publications
                                        .select_related('publication')
            ),
        })

    @action(detail=True, methods=['post'])
    def recalculate_h_index(self, request, pk=None):
        """POST /api/researchers/{id}/recalculate_h_index/"""
        researcher = self.get_object()
        new_h      = researcher.calculate_h_index()
        return Response({'h_index': new_h})

    # ========== NOUVELLES ACTIONS POUR OPENALEX ==========

    @action(detail=True, methods=['post'], url_path='verify-orcid')
    def verify_orcid(self, request, pk=None):
        """
        POST /api/researchers/{id}/verify-orcid/
        Vérifie un ORCID sur OpenAlex sans le sauvegarder
        Body : { "orcid": "0000-0002-1825-0097" }
        """
        researcher = self.get_object()
        orcid = request.data.get('orcid', '').strip()

        # Vérifier que c'est le chercheur lui-même ou un admin
        if request.user.user_id != researcher.user.id and not request.user.is_staff:
            return Response(
                {'error': 'Vous ne pouvez vérifier que votre propre ORCID.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not orcid:
            return Response(
                {'error': 'ORCID requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Nettoyer l'URL si besoin
        if "orcid.org/" in orcid:
            orcid = orcid.split("orcid.org/")[-1].strip()

        # Vérifier doublon (sauf si c'est le même chercheur)
        if Researcher.objects.filter(orcid=orcid).exclude(pk=researcher.pk).exists():
            return Response(
                {'valid': False, 'error': 'Cet ORCID est déjà associé à un autre compte.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérification OpenAlex
        result = verify_orcid(orcid)
        if not result['valid']:
            return Response(
                {'valid': False, 'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'valid': True,
            'message': 'ORCID vérifié avec succès sur OpenAlex.',
            'profile': result['profile']
        })

    @action(detail=True, methods=['post'], url_path='save-orcid')
    def save_orcid(self, request, pk=None):
        """
        POST /api/researchers/{id}/save-orcid/
        Sauvegarde l'ORCID et lance la synchronisation des publications
        Body : { "orcid": "0000-0002-1825-0097" }
        """
        researcher = self.get_object()
        orcid = request.data.get('orcid', '').strip()

        # Vérifier que c'est le chercheur lui-même ou un admin
        if request.user.id != researcher.user.id and not request.user.is_staff:
            return Response(
                {'error': 'Vous ne pouvez modifier que votre propre ORCID.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not orcid:
            return Response(
                {'error': 'ORCID requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Nettoyer l'URL si besoin
        if "orcid.org/" in orcid:
            orcid = orcid.split("orcid.org/")[-1].strip()

        # Vérifier doublon
        if Researcher.objects.filter(orcid=orcid).exclude(pk=researcher.pk).exists():
            return Response(
                {'error': 'Cet ORCID est déjà associé à un autre compte.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérification finale OpenAlex
        result = verify_orcid(orcid)
        if not result['valid']:
            return Response(
                {'valid': False, 'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Sauvegarder l'ORCID
        old_orcid = researcher.orcid
        researcher.orcid = orcid
        researcher.save(update_fields=['orcid'])

        # Mettre à jour h_index si disponible
        h_index = result['profile'].get('h_index', 0)
        if h_index:
            researcher.h_index = h_index
            researcher.save(update_fields=['h_index'])

        # Lancer la synchronisation
        try:
            stats = sync_researcher(orcid)
        except Exception as e:
             logger.error(f"Erreur sync ORCID {orcid}: {e}")
             stats = {'created': 0, 'updated': 0, 'errors': 1}

        return Response({
            'message': 'ORCID sauvegardé avec succès.',
            'orcid': orcid,
            'old_orcid': old_orcid,
            'profile': result['profile'],
            'sync_stats': {
                'publications_created': stats.get('created', 0),
                'publications_updated': stats.get('updated', 0),
                'h_index': researcher.h_index,
            }
        })

    @action(detail=True, methods=['post'], url_path='sync-publications')
    def sync_publications(self, request, pk=None):
        """
        POST /api/researchers/{id}/sync-publications/
        Relance la synchronisation des publications depuis OpenAlex
        """
        researcher = self.get_object()

        # Vérifier que c'est le chercheur lui-même ou un admin
        if request.user.id != researcher.user.id and not request.user.is_staff:
            return Response(
                {'error': 'Vous ne pouvez synchroniser que vos propres publications.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not researcher.orcid:
            return Response(
                {'error': 'Aucun ORCID associé à ce chercheur.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lancer la synchronisation
        stats = sync_researcher(researcher.orcid)

        return Response({
            'message': 'Synchronisation terminée.',
            'orcid': researcher.orcid,
            'stats': {
                'publications_created': stats.get('created', 0),
                'publications_updated': stats.get('updated', 0),
                'h_index': researcher.h_index,
            }
        })

    @action(detail=True, methods=['post'], url_path='remove-orcid')
    def remove_orcid(self, request, pk=None):
        """
        POST /api/researchers/{id}/remove-orcid/
        Supprime l'ORCID du chercheur
        """
        researcher = self.get_object()

        # Vérifier que c'est le chercheur lui-même ou un admin
        if request.user.id != researcher.user.id and not request.user.is_staff:
            return Response(
                {'error': 'Vous ne pouvez supprimer que votre propre ORCID.'},
                status=status.HTTP_403_FORBIDDEN
            )

        old_orcid = researcher.orcid
        researcher.orcid = None
        researcher.h_index = 0
        researcher.save(update_fields=['orcid', 'h_index'])

        return Response({
            'message': 'ORCID supprimé avec succès.',
            'old_orcid': old_orcid
        })

    @action(detail=False, methods=['get'], url_path='me/stats')
    def my_stats(self, request):
        """
        GET /api/researchers/me/stats/
        Statistiques du chercheur connecté
        """
        try:
            researcher = request.user.researcher_profile
        except Researcher.DoesNotExist:
            return Response(
                {'error': 'Vous n\'avez pas de profil chercheur.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({
            'h_index': researcher.h_index,
            'pub_count': researcher.user.coauthored_publications.count(),
            'orcid': researcher.orcid,
            'research_field': researcher.research_field,
            'total_citations': sum(
                ca.publication.citation_count
                for ca in researcher.user.coauthored_publications
                                        .select_related('publication')
            ),
        })

    @action(detail=False, methods=['patch'], url_path='me/update-profile')
    def update_my_profile(self, request):
        """
        PATCH /api/researchers/me/update-profile/
        Met à jour le profil du chercheur connecté
        """
        try:
            researcher = request.user.researcher_profile
        except Researcher.DoesNotExist:
            return Response(
                {'error': 'Vous n\'avez pas de profil chercheur.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ResearcherUpdateSerializer(
            researcher, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
    @action(detail=True, methods=['post'], url_path='connect-orcid')
    def connect_orcid(self, request, pk=None):
        """
        POST /api/researchers/{id}/connect-orcid/
        Vérifie l'ORCID puis synchronise automatiquement les données OpenAlex
        """

        researcher = self.get_object()
        orcid = request.data.get("orcid", "").strip()

        # sécurité
        if request.user.id != researcher.user.id and not request.user.is_staff:
            return Response(
                {"error": "Vous ne pouvez modifier que votre propre ORCID."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not orcid:
            return Response(
                {"error": "ORCID requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # nettoyage
        if "orcid.org/" in orcid:
            orcid = orcid.split("orcid.org/")[-1].strip()

        # vérifier doublon
        if Researcher.objects.filter(orcid=orcid).exclude(pk=researcher.pk).exists():
            return Response(
                {"error": "Cet ORCID est déjà utilisé."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ─── Vérification OpenAlex ───
        result = verify_orcid(orcid)

        if not result["valid"]:
            return Response(
                {"error": result["error"]},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile = result["profile"]

        # ─── Sauvegarder ORCID ───
        researcher.orcid = orcid
        researcher.h_index = profile.get("h_index", 0)
        researcher.save(update_fields=["orcid", "h_index"])

        # ─── Sync publications ───
        try:
            stats = sync_researcher(orcid)
        except Exception as e:
            logger.error(f"Erreur sync ORCID {orcid}: {e}")
            return Response(
                {"error": "Erreur lors de la synchronisation"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "message": "ORCID connecté et synchronisé avec succès.",
            "profile": profile,
            "sync": {
                "publications_created": stats.get("created", 0),
                "publications_updated": stats.get("updated", 0),
                "coauthors": stats.get("coauthors", 0),
                "citations": stats.get("citations", 0),
                "h_index": researcher.h_index,
            }
        })


# ─── Admin ────────────────────────────────────────────────────────────────────

class AdminViewSet(viewsets.ModelViewSet):
    queryset           = Admin.objects.select_related('user')
    serializer_class   = AdminSerializer
    permission_classes = [IsAdminUser]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['role']
    search_fields      = ['user__username', 'user__email']


# ─── LabManager ───────────────────────────────────────────────────────────────

class LabManagerViewSet(viewsets.ModelViewSet):
    queryset           = LabManager.objects.select_related('user', 'laboratory')
    serializer_class   = LabManagerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['laboratory']
    search_fields      = ['user__username', 'user__first_name', 'user__last_name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


# ─── TeamLeader ───────────────────────────────────────────────────────────────

class TeamLeaderViewSet(viewsets.ModelViewSet):
    queryset           = TeamLeader.objects.select_related('user', 'team')
    serializer_class   = TeamLeaderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['team']
    search_fields      = ['user__username', 'user__first_name', 'user__last_name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]