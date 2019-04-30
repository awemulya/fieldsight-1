from datetime import datetime

from django.core.urlresolvers import reverse
from fcm.utils import get_device_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from onadata.apps.fieldsight.models import Site, Project, Organization, Region
from onadata.apps.staff.models import StaffProject


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="user_roles")
    group = models.ForeignKey(Group)
    started_at = models.DateTimeField(default=datetime.now)
    ended_at = models.DateTimeField(blank=True, null=True, db_index=True)
    site = models.ForeignKey(Site, null=True, blank=True, related_name='site_roles')
    project = models.ForeignKey(Project, null=True, blank=True, related_name='project_roles')
    organization = models.ForeignKey(Organization, null=True, blank=True, related_name='organization_roles')
    staff_project = models.ForeignKey(StaffProject, null=True, blank=True, related_name='staff_project_roles')
    region = models.ForeignKey(Region, null=True, blank=True, related_name='region_roles')

    logs = GenericRelation('eventlog.FieldSightLog')

    def __unicode__(self):
        return 'user: {}\'s role : {}'.format(self.user.__unicode__(), self.group.__unicode__())

    def as_json(self):
        return dict(
            user = self.user.get_full_name(), email = self.user.email
            )

    def getname(self):
        return str("role")

    # class Meta:
    #     unique_together = ('user', 'group', 'organization', 'project', 'site', 'ended_at',)

    def get_absolute_url(self):
        return reverse('users:profile', kwargs={'pk': self.user.pk})

    def clean(self):
        if self.group.name in ['Site Supervisor', 'Reviewer'] and not self.site_id:
            raise ValidationError({
                'site': ValidationError(_('Missing site.'), code='required'),
            })

        if self.group.name == 'Project Manager' and not self.project_id:
            raise ValidationError({
                'project': ValidationError(_('Missing Project.'), code='required'),
            })

        if self.group.name == 'Organization Admin' and not self.organization_id:
            raise ValidationError({
                'organization': ValidationError(_('Missing Organization.'), code='required'),
            })

        if self.group.name in ['Region Supervisor', 'Region Reviewer'] and not self.region_id:
            raise ValidationError({
                'region': ValidationError(_('Missing Region.'), code='required'),
            })

        if self.user and UserRole.objects.filter(user=self.user, group=self.group, project=self.project,
                                                 region=self.region, site=self.site).exists():
            raise ValidationError({
                'user': ValidationError(_('User Role Already Exists.')),
            })

    def save(self, *args, **kwargs):
        if self.group.name == 'Super Admin':
            self.organization = None
            self.project = None
            self.site = None
            self.region = None

        elif self.group.name == 'Organization Admin':
            self.project = None
            self.site = None
            self.region = None

        elif self.group.name == 'Project Manager':
            self.site = None
            self.region = None
            self.organization = self.project.organization

        elif self.group.name == 'Project Doner':
            self.site = None
            self.region = None
            self.organization = self.project.organization

        elif self.group.name in ['Site Supervisor', 'Reviewer']:
            self.project = self.site.project
            self.organization = self.site.project.organization

        elif self.group.name in ['Region Supervisor', 'Region Reviewer']:
            self.project = self.region.project
            self.organization = self.project.organization

        elif self.group.name == 'Staff Project Manager':
            self.organization = None
            self.project = None
            self.site = None
            self.region = None

        super(UserRole, self).save(*args, **kwargs)

    def update(self, *args, **kwargs):
        if self.group.name == 'Super Admin':
            self.organization = None
            self.project = None
            self.site = None
            self.region = None

        elif self.group.name == 'Organization Admin':
            self.project = None
            self.site = None
            self.region = None

        elif self.group.name == 'Project Manager':
            self.site = None
            self.region = None
            self.organization = self.project.organization

        elif self.group.name in ['Site Supervisor', 'Reviewer']:
            self.project = self.site.project
            self.organization = self.site.project.organization

        elif self.group.name in ['Region Supervisor', 'Region Reviewer']:
            self.project = self.region.project
            self.organization = self.project.organization

        super(UserRole, self).update(*args, **kwargs)

    @staticmethod
    def is_active(user,group):
        return UserRole.objects.filter(user=user, group__name=group,ended_at=None).count()

    @staticmethod
    def get_active_roles(user):
        return UserRole.objects.filter(user=user,ended_at=None).select_related('group', 'organization')

    @staticmethod
    def get_active_site_roles(user):
        return UserRole.objects.filter(user=user, ended_at=None, group__name="Site Supervisor", site__isnull=False, site__is_active=True).\
            select_related('project', 'site', 'site__type', 'project__organization', 'project__type')\

    @staticmethod
    def get_active_site_roles_count(user):
        return UserRole.objects.filter(user=user, ended_at=None, group__name="Site Supervisor", site__isnull=False, site__is_active=True).count()

    @staticmethod
    def get_active_site_roles_exists(user):
        return UserRole.objects.filter(user=user, ended_at=None).filter(Q(group__name="Site Supervisor", site__isnull=False, site__is_active=True)|
                                                                        Q(group__name="Region Supervisor", region__is_active=True)).exists()

    @staticmethod
    def get_roles_supervisor(user, project_id):
        return True if UserRole.objects.filter(user=user, ended_at=None, group__name="Site Supervisor", site__isnull=False, site__is_active=True,
                                               project__id=project_id).select_related('group', 'project')\
                                                    .exists() else False

    @staticmethod
    def project_managers(project):
        return UserRole.objects.filter(project=project, ended_at=None, group__name="Project Manager").\
            select_related('group', 'project')

    @staticmethod
    def organization_admins(organization):
        return UserRole.objects.filter(organization=organization, ended_at=None, group__name="Organization Admin").\
            select_related('group', 'organization')\

    @staticmethod
    def central_engineers(project):
        return UserRole.objects.filter(project=project, ended_at=None, group__name="Reviewer").\
            select_related('group', 'project')

    @property
    def has_multiple_project_roles(self):
        return UserRole.objects.filter(user=self.user, group__name__in=['Project Manager', 'Reviewer'], organization=self.organization).count() > 1

    @property
    def both_project_roles(self):
        return UserRole.objects.filter(user=self.user, group__name__in=['Project Manager', 'Reviewer'], organization=self.organization)


@receiver(post_save, sender=UserRole)
def create_messages(sender, instance, created,  **kwargs):
    if created and instance.site is not None and instance.group.name in ["Site Supervisor"]:
        Device = get_device_model()
        if Device.objects.filter(name=instance.user.email).exists():
            message = {'notify_type':'Assign Site', 'site':{'name': instance.site.name, 'id': instance.site.id}, 'project':{'name': instance.project.name, 'id': instance.project.id}}
            try:
                Device.objects.filter(name=instance.user.email).send_message(message)
            except:
                pass

post_save.connect(create_messages, sender=UserRole)
