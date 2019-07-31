from datetime import datetime
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Q

from rest_framework import serializers
from onadata.apps.userrole.models import UserRole
from onadata.apps.fieldsight.models import UserInvite, Project, Region, Site
from onadata.apps.fsforms.models import FInstance

FORM_STATUS = {0: 'Pending', 1: "Rejected", 2: 'Flagged', 3: 'Approved'}


class MyProjectSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='project_id')
    name = serializers.CharField(source='project.name')
    has_project_access = serializers.SerializerMethodField()

    class Meta:
        model = UserRole
        fields = ('id', 'name', 'has_project_access')

    def get_has_project_access(self, obj):
        if obj.group.name == "Project Manager" or obj.group.name == "Project Donor":
            has_access = True

        else:
            has_access = False

        return has_access

    def get_project_url(self, obj):
        has_project_access = self.get_has_project_access(obj)

        if has_project_access:
            project_url = settings.SITE_URL + obj.project.get_absolute_url()

            return project_url


class MyRegionSerializer(serializers.ModelSerializer):
    total_sites = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    region_url = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = ('id', 'identifier', 'name', 'total_sites', 'role', 'region_url')

    def get_total_sites(self, obj):
        return obj.get_sites_count()

    def get_role(self, obj):
        user = self.context['request'].user
        is_project_manager_or_team_admin = user.user_roles.all().filter(Q(group__name="Project Manager", project=obj.project)|
                                                                         Q(group__name="Organization Admin",
                                                                           organization=obj.project.organization)).exists()
        if is_project_manager_or_team_admin:
            group = None

        else:

            obj = obj.region_roles.select_related('group').filter(user=user)

            if len(obj) > 1:
                group = "Region Supervisor"
            else:
                group = obj.get().group.name

        return group

    def get_region_url(self, obj):
        return settings.SITE_URL + obj.get_absolute_url()


class MySiteSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    submissions = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    site_url = serializers.SerializerMethodField()
    region = serializers.CharField(source='region.name')

    class Meta:
        model = Site
        fields = ('id', 'identifier', 'name', 'address', 'site_url', 'region', 'role', 'submissions', 'progress', 'status')

    def get_role(self, obj):
        user = self.context['request'].user
        is_project_manager_or_team_admin = user.user_roles.all().filter(Q(group__name="Project Manager", project=obj.project)|
                                                          Q(group__name="Organization Admin", organization=obj.project.organization)).exists()

        if is_project_manager_or_team_admin:
            group = None

        else:
            obj = obj.site_roles.select_related('group').filter(user=user)

            if len(obj) > 1:
                group = "Site Supervisor"
            else:
                group = obj.get().group.name

        return group

    def get_submissions(self, obj):
        response = obj.get_site_submission_count()
        submissions = response['outstanding'] + response['flagged'] + response['approved'] + response['rejected']

        return submissions

    def get_status(self, obj):

        try:
            if obj.site_instances.all():
                return FORM_STATUS[obj.current_status]
        except:
            return None

    def get_progress(self, obj):

        if obj.current_progress:
            return obj.current_progress
        else:
            return 0

    def get_site_url(self, obj):
        return settings.SITE_URL + obj.get_absolute_url()

    def get_region_url(self, obj):
        if obj.region:
            return settings.SITE_URL + obj.region.get_absolute_url()


class MyRolesSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    # post = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    has_organization_access = serializers.SerializerMethodField()
    team_url = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()
    id = serializers.IntegerField(source='organization.id')

    class Meta:
        model = UserRole
        fields = ('id', 'name', 'address', 'logo', 'has_organization_access', 'team_url', 'projects')

    def get_name(self, obj):
        return obj.organization.name

    def get_address(self, obj):
        return obj.organization.address

    def get_logo(self, obj):
        return obj.organization.logo.url

    def get_has_organization_access(self, obj):
        user = self.context['user']
        if obj.organization_id in user.user_roles.filter(group__name="Organization Admin").values_list('organization_id', flat=True):
            has_access = True

        else:
            has_access = False

        return has_access

    def get_projects(self, obj):
        org_admin = self.get_has_organization_access(obj)

        if org_admin:
            data = Project.objects.filter(organization=obj.organization, is_active=True)
            roles = [{'id': r.id, 'name': r.name, 'has_project_access': True} for r in data]
            # roles = [{'id': proj.id, 'name': proj.name, 'project_url': settings.SITE_URL + proj.get_absolute_url()} for proj in data]

        else:
            data = UserRole.objects.filter(user=obj.user, organization=obj.organization).select_related('user', 'group', 'site', 'organization',
                                                                      'staff_project', 'region').filter(Q(group__name="Project Manager", project__is_active=True)|
                                                                    Q(group__name="Site Supervisor", site__is_active=True)|
                                                                    Q(group__name="Site Reviewer", site__is_active=True)|
                                                                    Q(group__name="Region Reviewer", region__is_active=True)|
                                                                    Q(group__name="Region Supervisor", region__is_active=True)|
                                                                    Q(group__name="Project Donor", project__is_active=True)
                                                                                                        ).distinct('project')
            roles = MyProjectSerializer(data, many=True).data
        return roles

    def get_team_url(self, obj):
        return settings.SITE_URL + obj.organization.get_absolute_url()

    def to_representation(self, obj):
        data = super(MyRolesSerializer, self).to_representation(obj)
        user = self.context['user']

        if obj.organization_id not in user.user_roles.filter(group__name="Organization Admin").values_list('organization_id', flat=True):

            data.pop('team_url')

        return data
    #
    # def get_post(self, obj):
    #
    #     return obj.group.name

    # def get_name(self, obj):
    #
    #     if obj.group.name == 'Region Supervisor' or obj.group.name == 'Region Reviewer':
    #         return obj.region.name
    #
    #     elif obj.group.name == 'Project Manager' or obj.group.name == 'Project Donor' or obj.group.name == 'Staff Project Manager':
    #         return obj.project.name
    #
    #     elif obj.group.name == 'Site Supervisor' or obj.group.name == 'Site Reviewer':
    #         return obj.site.name
    #
    #     elif obj.group.name == 'Organization Admin':
    #         return obj.organization.name

    # def get_address(self, obj):
    #
    #     if obj.group.name == 'Region Supervisor' or obj.group.name == 'Region Reviewer':
    #         return None
    #
    #     elif obj.group.name == 'Project Manager' or obj.group.name == 'Project Donor' or obj.group.name == 'Staff Project Manager':
    #         return obj.project.address
    #
    #     elif obj.group.name == 'Site Supervisor' or obj.group.name == 'Site Reviewer':
    #         return obj.site.address
    #
    #     elif obj.group.name == 'Organization Admin':
    #         return obj.organization.address


class UserInvitationSerializer(serializers.ModelSerializer):
    group = serializers.CharField(source='group.name')
    by_user = serializers.CharField(source='by_user.username')
    current_user = serializers.SerializerMethodField()

    class Meta:
        model = UserInvite
        fields = ('id', 'by_user', 'group', 'current_user')

    def get_current_user(self, obj):

        user = User.objects.get(email=obj.email)
        return user.username


class LatestSubmissionSerializer(serializers.ModelSerializer):
    detail_url = serializers.SerializerMethodField()
    form = serializers.SerializerMethodField()
    date =serializers.SerializerMethodField()

    class Meta:
        model = FInstance
        fields = ('id', 'date', 'form', 'detail_url')

    def get_detail_url(self, obj):
        return '/#/submission-details/{}'.format(obj.id)

    def get_form(self, obj):
        if obj.project_fxf:
            return obj.project_fxf.xf.title
        elif obj.site_fxf:
            return obj.site_fxf.xf.title

    def get_date(self, obj):
        return datetime.strftime(obj.date, '%Y-%m-%d %H:%M:%S')

