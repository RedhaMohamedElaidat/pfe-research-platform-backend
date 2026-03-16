# institution/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from institution.models import Country, Wilaya, Commune, Ville, Institution
from institution.serializers import (
    CountrySerializer, WilayaSerializer, CommuneSerializer,
    VilleSerializer, InstitutionSerializer, InstitutionDetailSerializer
)


class CountryViewSet(viewsets.ModelViewSet):
    queryset           = Country.objects.all()
    serializer_class   = CountrySerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['name']
    ordering           = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class WilayaViewSet(viewsets.ModelViewSet):
    queryset           = Wilaya.objects.select_related('country')
    serializer_class   = WilayaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['country']
    search_fields      = ['name']
    ordering           = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class CommuneViewSet(viewsets.ModelViewSet):
    queryset           = Commune.objects.select_related('wilaya')
    serializer_class   = CommuneSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['wilaya']
    search_fields      = ['name']
    ordering           = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class VilleViewSet(viewsets.ModelViewSet):
    queryset           = Ville.objects.select_related('commune__wilaya')
    serializer_class   = VilleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['commune']
    search_fields      = ['name']
    ordering           = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class InstitutionViewSet(viewsets.ModelViewSet):
    queryset           = Institution.objects.select_related('ville__commune__wilaya')
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['type', 'ville']
    search_fields      = ['name', 'description']
    ordering_fields    = ['name', 'type']
    ordering           = ['name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InstitutionDetailSerializer
        return InstitutionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """GET /api/institutions/{id}/stats/"""
        institution = self.get_object()
        return Response({
            'total_publications': institution.get_total_publications(),
            'average_h_index':    institution.get_average_h_index(),
            'top_researchers':    [
                {
                    'id':      u.user_id,
                    'name':    u.get_full_name(),
                    'h_index': getattr(getattr(u, 'researcher_profile', None), 'h_index', 0),
                }
                for u in institution.get_top_researchers(limit=10)
            ],
        })

    @action(detail=True, methods=['get'])
    def laboratories(self, request, pk=None):
        """GET /api/institutions/{id}/laboratories/"""
        from laboratory.models import Laboratory
        from laboratory.serializers import LaboratorySerializer
        institution = self.get_object()
        labs = Laboratory.objects.filter(institution=institution)
        return Response(LaboratorySerializer(labs, many=True).data)