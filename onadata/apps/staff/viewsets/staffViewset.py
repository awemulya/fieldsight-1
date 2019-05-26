from __future__ import unicode_literals
import datetime
import json
from rest_framework import viewsets
from rest_framework.permissions import BasePermission

from django.http import HttpResponse

from onadata.apps.fsforms.enketo_utils import CsrfExemptSessionAuthentication
from onadata.apps.staff.models import Staff, Attendance, Team, STAFF_TYPES, GENDER_TYPES, Bank
from onadata.apps.staff.serializers.staffSerializer import StaffSerializer, AttendanceSerializer, TeamSerializer, BankSerializer
from rest_framework.authentication import BasicAuthentication
SAFE_METHODS = ('GET', 'POST')


def staffdesignations(request):
    return HttpResponse(json.dumps(STAFF_TYPES), status=200)

def staffgender(request):
    return HttpResponse(json.dumps(GENDER_TYPES), status=200)

class TeamAccessPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated():
            return False
        
        if request.group:
            if request.group.name == "Super Admin":
                return True

        team_leader = Team.objects.filter(is_deleted=False, pk=view.kwargs.get('team_id'), leader_id = request.user.id)
        
        if team_leader:
            return True

        return False

class BankViewSet(viewsets.ModelViewSet):
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    authentication_classes = (BasicAuthentication,)
    def filter_queryset(self, queryset):
        return queryset

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.filter(is_deleted=False)
    serializer_class = TeamSerializer
    # authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
        
    def filter_queryset(self, queryset):
        queryset = queryset.filter(leader_id=self.request.user.id)
        return queryset

class StafflistViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.filter(is_deleted=False)
    serializer_class = StaffSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = (TeamAccessPermission,)
    # parser_classes = (MultiPartParser, FormParser,)

    def filter_queryset(self, queryset):
        try:
            queryset = queryset.filter(team_id=self.kwargs.get('team_id'))
        except:
            queryset = []
        return queryset


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.filter(is_deleted=False)
    serializer_class = StaffSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = (TeamAccessPermission,)
    # parser_classes = (MultiPartParser, FormParser,)

    def filter_queryset(self, queryset):
        try:
            queryset = queryset.filter(team_id=self.kwargs.get('team_id'))
        except:
            queryset = []
        return queryset

    def perform_create(self, serializer, **kwargs):
        serializer.save(created_by=self.request.user, team_id=self.kwargs.get('team_id'))
        return serializer

class StaffUpdateViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing sites.
    """
    queryset = Staff.objects.filter(is_deleted=False)
    serializer_class = StaffSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = (TeamAccessPermission,)

    def filter_queryset(self, queryset):

        return queryset.filter(pk=self.kwargs.get('pk', None), team_id=self.kwargs.get('team_id', None))

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceSerializer
    permission_classes = (TeamAccessPermission,)
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def filter_queryset(self, queryset):
        enddate = datetime.date.today()

        startdate = enddate - datetime.timedelta(days=7)
        queryset = queryset.filter(team_id=self.kwargs.get('team_id'), attendance_date__range=[startdate, enddate])
        return queryset

    def perform_create(self, serializer, **kwargs):
        data = serializer.save(submitted_by=self.request.user, team_id=self.kwargs.get('team_id'))
        return data