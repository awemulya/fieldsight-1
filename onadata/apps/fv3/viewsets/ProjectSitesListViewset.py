from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from onadata.apps.fieldsight.models import Site
from onadata.apps.fv3.serializers.ProjectSitesListSerializer import ProjectSitesListSerializer


class ProjectsitesPagination(PageNumberPagination):
    page_size = 200


class ProjectSitesListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Site.objects.filter(site__isnull=True).select_related('project',
                                                            'region', 'type')
    serializer_class = ProjectSitesListSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = ProjectsitesPagination

    def get_queryset(self):

        project_id = self.request.query_params.get('project', None)
        search_param = self.request.query_params.get('q', None)
        unassigned = self.request.query_params.get('region', None)

        if search_param and project_id and unassigned:
            return self.queryset.filter(Q(name__icontains=search_param) | Q(identifier__icontains=search_param),
                                        project_id=project_id, is_survey=False, is_active=True, region=None)

        if project_id and unassigned == "0":
            return self.queryset.filter(project_id=project_id, is_survey=False, is_active=True, region=None)

        if search_param and project_id:
            return self.queryset.filter(Q(name__icontains=search_param) | Q(identifier__icontains=search_param),
                                        project_id=project_id, is_survey=False, is_active=True)

        if project_id:
            return self.queryset.filter(project_id=project_id, is_survey=False, is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        try:
            page = self.paginate_queryset(queryset)

        except:
            return Response({"message": "Project Id is required."}, status=status.HTTP_204_NO_CONTENT)

        search_param = request.query_params.get('q', None)

        if page is not None:
            serializer = self.get_serializer(page, many=True)

            return self.get_paginated_response({'data': serializer.data, 'query': search_param})

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SubSitesListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Site.objects.select_related('project', 'region', 'type')
    serializer_class = ProjectSitesListSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = ProjectsitesPagination

    def get_queryset(self):

        site_id = self.request.query_params.get('site', None)
        search_param = self.request.query_params.get('q', None)

        if search_param and site_id:
            return self.queryset.filter(Q(name__icontains=search_param) | Q(identifier__icontains=search_param),
                                        site_id=site_id, is_survey=False,
                                        is_active=True)

        if site_id:
            return self.queryset.filter(site_id=site_id, is_survey=False,
                                        is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        try:
            page = self.paginate_queryset(queryset)

        except:
            return Response({"message": "Site Id is required."},
                            status=status.HTTP_204_NO_CONTENT)

        search_param = request.query_params.get('q', None)

        if page is not None:
            serializer = self.get_serializer(page, many=True)

            return self.get_paginated_response({'data': serializer.data, 'query': search_param})

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)