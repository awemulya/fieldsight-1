from __future__ import unicode_literals
import json
from django.db.models import Q, Count, Case, IntegerField, F, When
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.response import Response

from onadata.apps.fieldsight.models import Site
from onadata.apps.fsforms.models import Schedule, Days, FieldSightXF, FInstance
from onadata.apps.fsforms.serializers.ScheduleSerializer import ScheduleSerializer, DaysSerializer
from rest_framework.pagination import PageNumberPagination

class LargeResultsSetPagination(PageNumberPagination):
    page_size = 10


class ScheduleViewset(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing scheduless.
    """
    queryset = Schedule.objects.filter(schedule_forms__isnull=False, schedule_forms__is_deleted=False)
    serializer_class = ScheduleSerializer
    # pagination_class = LargeResultsSetPagination

    def filter_queryset(self, queryset):
        if self.request.user.is_anonymous():
            self.permission_denied(self.request)
        is_project = self.kwargs.get('is_project', None)
        pk = self.kwargs.get('pk', None)
        if is_project == "1":
            queryset = queryset.filter(project__id=pk)
            return queryset.annotate(response_count=Count("schedule_forms__project_form_instances")).select_related('schedule_forms', 'schedule_forms__xf', 'schedule_forms__em')
        else:
            project_id = get_object_or_404(Site, pk=pk).project.id
            queryset = queryset.filter(Q(site__id=pk, schedule_forms__from_project=False)
                                       | Q(project__id=project_id))
            return queryset.annotate(
                site_response_count=Count("schedule_forms__site_form_instances", ),
                response_count=Count(Case(
                    When(project__isnull=False, schedule_forms__project_form_instances__site__id=pk, then=F('schedule_forms__project_form_instances')),
                    output_field=IntegerField(),
                ), distinct=True)

            ).select_related('schedule_forms','schedule_forms__xf', 'schedule_forms__em')

    def get_serializer_context(self):
        return self.kwargs

    def perform_create(self, serializer):
        # from rest_framework.exceptions import ValidationError

        data = self.request.data

        # if "form" not in data:
        #     raise ValidationError({
        #         "form": "No Form Selected ",
        #     })
        # if data.has_key('site'):
        #     if FieldSightXF.objects.filter(xf=data["form"], is_scheduled=True, site=data["site"]).exists():
        #         raise ValidationError({
        #             "form": "Form Already Used ",
        #         })
        #     if FieldSightXF.objects.filter(xf=data["form"],is_scheduled=True, project=data["project"]).exists():
        #         raise ValidationError({
        #             "form": "Form Already Used ",
        #         })

        schedule = serializer.save()



        fxf = FieldSightXF(xf_id=data["xf"], is_scheduled=True, schedule=schedule, site=schedule.site,
                                    project=schedule.project, default_submission_status=data.get('default_submission_status', 0))
        if data.has_key("site"):
            fxf.is_deployed = True
            fxf.from_project = False
            fxf.save()
            noti = fxf.logs.create(source=self.request.user, type=19, title="Schedule",
                                  organization=fxf.site.project.organization,
                                  project = fxf.site.project,
                                  site = fxf.site, content_object=fxf, extra_object = fxf.site,
                                              extra_message='{0} form {1}'.format(fxf.form_type(), fxf.xf.title),
                                  description='{0} assigned new Schedule form  {1} to {2} '.format(
                                      self.request.user.get_full_name(),
                                      fxf.xf.title,
                                      fxf.site.name
                                  ))

        else:
            fxf.save()
            noti = fxf.logs.create(source=self.request.user, type=18, title="Schedule",
                      organization=fxf.project.organization,
                      project = fxf.project, content_object=fxf, extra_object=fxf.project, extra_message='{0} form {1}'.format(fxf.form_type(), fxf.xf.title),
                      description='{0} assigned new Schedule form  {1} to {2} '.format(
                          self.request.user.get_full_name(),
                          fxf.xf.title,
                          fxf.project.name
                      ))

        


class DayViewset(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for viewing and editing scheduless.
    """
    queryset = Days.objects.all()
    serializer_class = DaysSerializer
