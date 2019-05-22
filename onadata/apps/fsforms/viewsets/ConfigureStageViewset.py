from __future__ import unicode_literals

from django.db.models import Sum, F, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import rest_framework.status

from onadata.apps.fieldsight.models import Site
from onadata.apps.fsforms.models import Stage, EducationMaterial, DeployEvent, FInstance
from onadata.apps.fsforms.serializers.ConfigureStagesSerializer import StageSerializer, SubStageSerializer, \
    SubStageDetailSerializer, EMSerializer, DeploySerializer, FinstanceSerializer, FinstanceDataOnlySerializer
from onadata.apps.userrole.models import UserRole
from onadata.apps.fieldsight.models import Region


class StageListViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Main Stages.
    """
    queryset = Stage.objects.filter(stage_forms__isnull=True, stage__isnull=True).order_by('order', 'date_created')
    serializer_class = StageSerializer

    def filter_queryset(self, queryset):
        if self.request.user.is_anonymous():
            self.permission_denied(self.request)
        is_project = self.kwargs.get('is_project', None)
        pk = self.kwargs.get('pk', None)
        if is_project == "1":
            queryset = queryset.filter(project__id=pk)
        else:
            project_id = get_object_or_404(Site, pk=pk).project.id
            queryset = queryset.filter(Q(site__id=pk, project_stage_id=0) |Q (project__id=project_id))
        return queryset.annotate(sub_stage_weight=Sum(F('parent__weight')))

    def retrieve_by_id(self, request, *args, **kwargs):
        instance = Stage.objects.get(pk=kwargs.get('pk'))
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = Stage.objects.get(pk=kwargs.get('pk'))
        name = self.request.data.get('name', False)
        tags = self.request.data.get('tags', [])
        if not name:
            return Response({'error':'No Stage Name Provided'}, status=status.HTTP_400_BAD_REQUEST)
        desc = self.request.data.get('description', "")
        instance.name = name
        instance.description = desc
        instance.tags = tags
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_context(self):
        return {'request': self.request, 'kwargs': self.kwargs,}


class SubStageListViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Main Stages.
    """
    queryset = Stage.objects.filter(stage__isnull=False).order_by('order', 'date_created')
    serializer_class = SubStageSerializer

    def filter_queryset(self, queryset):
        if self.request.user.is_anonymous():
            self.permission_denied(self.request)
        stage_id = self.kwargs.get('stage_id', None)
        queryset = queryset.filter(stage__id=stage_id)
        return queryset

    def get_serializer_context(self):
        return {'request': self.request, 'kwargs': self.kwargs,}


class SubStageDetailViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Sub Stages.
    """
    queryset = Stage.objects.all().select_related('stage_forms', 'em').order_by('order', 'date_created')
    serializer_class = SubStageDetailSerializer

    # def filter_queryset(self, queryset):
    #     if self.request.user.is_anonymous():
    #         self.permission_denied(self.request)
    #     stage_id = self.kwargs.get('stage_id', None)
    #     queryset = queryset.filter(stage__id=stage_id)
    #     return queryset

    def get_serializer_context(self):
        return {'request': self.request, 'kwargs': self.kwargs,}


class EmViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing em of Stages.
    """
    queryset = EducationMaterial.objects.all()
    serializer_class = EMSerializer

    def retrieve_by_id(self, request, *args, **kwargs):
        stage = Stage.objects.get(pk=kwargs.get('pk'))
        try:
            instance = stage.em
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except:
            return Response({})

    # def update(self, request, *args, **kwargs):
    #     instance = Stage.objects.get(pk=kwargs.get('pk'))
    #     name = self.request.data.get('name', False)
    #     if not name:
    #         return Response({'error':'No Stage Name Provided'}, status=status.HTTP_400_BAD_REQUEST)
    #     desc = self.request.data.get('description', "")
    #     instance.name = name
    #     instance.description = desc
    #     instance.save()
    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)

    def get_serializer_context(self):
        return {'request': self.request, 'kwargs': self.kwargs,}


class DeployViewset(viewsets.ModelViewSet):
    queryset = DeployEvent.objects.all()
    serializer_class = DeploySerializer

class LargeResultsSetPagination(PageNumberPagination):
    page_size = 100
    # page_size_query_param = 'page_size'
    # max_page_size = 10000


class FInstanceViewset(viewsets.ReadOnlyModelViewSet):
    queryset = FInstance.objects.all()
    serializer_class = FinstanceDataOnlySerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        sites = list(UserRole.objects.filter(user=self.request.user, group__name="Site Supervisor", ended_at__isnull=False).distinct('site').values_list('site', flat=True))
        # if UserRole.objects.filter(user=self.request.user, group__name="Region Supervisor", ended_at__isnull=False).exists():
        try:
            regions_id = UserRole.objects.filter(user=self.request.user, group__name="Region Supervisor", ended_at__isnull=False).distinct('region').values_list('region', flat=True)

            # assume maximum recursion depth is 3
            region_sites = Site.objects.filter(Q(region_id__in=regions_id) | Q(region_id__parent__in=regions_id) | Q(region_id__parent__parent__in=regions_id)).values_list('id',
                                                                                                      flat=True)
            sites += region_sites
        except:
            pass

        return self.queryset.filter(site__in=sites).select_related('submitted_by', 'site_fxf',  'project_fxf').order_by("-date")
