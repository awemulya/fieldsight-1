from __future__ import unicode_literals
from django import forms

from PIL import Image
from django.core.files import File
from django.contrib.auth.models import User, Group
from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse_lazy
from django.forms import TextInput
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from registration import forms as registration_forms

from onadata.apps.fieldsight.helpers import AdminImageWidget
from .utils.forms import HTML5BootstrapModelForm, KOModelForm

from .models import Organization, Project, Site, BluePrints, Region, SiteType
from onadata.apps.geo.models import GeoLayer

from onadata.apps.userrole.models import UserRole
from django.core.exceptions import ValidationError
import StringIO
import mimetypes
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
USERNAME_REGEX = r'^[a-z][a-z0-9_]+$'
USERNAME_MAX_LENGTH = 30
USERNAME_INVALID_MESSAGE = _(
    'A username may only contain lowercase letters, numbers, and '
    'underscores (_).'
)


class RegistrationForm(registration_forms.RegistrationFormUniqueEmail):

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['organization'].choices = [(org.id, org.name) for org in Organization.objects.all()]
        self.fields['organization'].empty_label = None

    organization = forms.ChoiceField(widget = forms.Select(), required=False)
    username = forms.RegexField(
        regex=USERNAME_REGEX,
        max_length=USERNAME_MAX_LENGTH,
        label=_("Username"),
        error_messages={'invalid': USERNAME_INVALID_MESSAGE}
    )
    name = forms.CharField(
        label=_('Full Name'),
        required=True,
    )

    is_active = forms.BooleanField(
        label=_('Active'),
        required=False,
        initial=True
    )


    class Meta:
        model = User
        fields = [
            'name',
            'username',
            'email',
            # The 'password' field appears without adding it here; adding it
            # anyway results in a duplicate
        ]


class OrganizationForm(forms.ModelForm):
    x = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height = forms.FloatField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
        if not self.fields['location'].initial:
            self.fields['location'].initial = Point(85.3240, 27.7172,srid=4326)
        self.fields['type'].empty_label = None

    class Meta:
        model = Organization
        exclude = ['is_active']
        # exclude = ['organizaton']
        widgets = {
        'is_active': forms.HiddenInput(),
        'location': forms.HiddenInput(),
        'address': forms.TextInput(),
        'logo': AdminImageWidget()
        }

    def save(self):
        photo = super(OrganizationForm, self).save()
        x = self.cleaned_data.get('x')
        y = self.cleaned_data.get('y')
        w = self.cleaned_data.get('width')
        h = self.cleaned_data.get('height')

        if x is not None and y is not None:
            image = Image.open(photo.logo)
            cropped_image = image.crop((x, y, w+x, h+y))
            resized_image = cropped_image.resize((200, 200), Image.ANTIALIAS)
            # resized_image.save(photo.logo.path)
            resized_image_file = StringIO.StringIO()
            mime = mimetypes.guess_type(photo.logo.name)[0]
            plain_ext = mime.split('/')[1]
            resized_image.save(resized_image_file, plain_ext)
            default_storage.delete(photo.logo.name)
            default_storage.save(photo.logo.name, ContentFile(resized_image_file.getvalue()))
            resized_image_file.close()
        return photo


    def clean(self):
        lat = self.data.get("Longitude","85.3240")
        long = self.data.get("Latitude","27.7172")
        p = Point(round(float(lat), 6), round(float(long), 6),srid=4326)
        self.cleaned_data["location"] = p
        super(OrganizationForm, self).clean()


class AssignOrgAdmin(HTML5BootstrapModelForm, KOModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(AssignOrgAdmin, self).__init__(*args, **kwargs)
        role = kwargs.get('instance')
        if role is not None:
            old_admins = role.organization.get_staffs
            old_admins_id = [admin[0] for admin in old_admins]
            old_admins_id.append(settings.ANONYMOUS_USER_ID)
            if hasattr(self.request, "organization"):
                if self.request.organization:
                    users = User.objects.filter(user_profile__organization=self.request.organization, is_active=True).\
                        filter(id__in=old_admins_id)
                else:
                    users = User.objects.filter(is_active=True).exclude(id__in=old_admins_id)
            else:
                users = User.objects.filter(is_active=True).exclude(id__in=old_admins_id)
            self.fields['user'].queryset = users
            self.fields['organization'].choices = old_admins

    class Meta:
        fields = ['user', 'group', 'organization']
        model = UserRole
        widgets = {
            'user': forms.Select(attrs={'class': 'selectize', 'data-url': reverse_lazy('role:user_add')}),
            'group': forms.HiddenInput(),
            'organization': forms.HiddenInput()
        }


class SetProjectManagerForm(HTML5BootstrapModelForm, KOModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(SetProjectManagerForm, self).__init__(*args, **kwargs)
        role = kwargs.get('instance')
        if role is not None:
            old_admins = role.project.get_staffs_id
            users = User.objects.filter().exclude(id=settings.ANONYMOUS_USER_ID).exclude(id__in=old_admins)
            if hasattr(self.request, "organization"):
                if self.request.organization:
                    users = users.filter(user_profile__organization=self.request.organization)
            self.fields['user'].queryset = users

    class Meta:
        fields = ['user','group','project']
        model = UserRole
        widgets = {
            'user': forms.Select(attrs={'class': 'selectize', 'data-url': reverse_lazy('role:user_add')}),
            'group': forms.HiddenInput(),
            'project': forms.HiddenInput()
        }


class SetSupervisorForm(HTML5BootstrapModelForm, KOModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(SetSupervisorForm, self).__init__(*args, **kwargs)
        role = kwargs.get('instance')
        if role is not None:
            old_pm = role.site.get_supervisor_id
            users = User.objects.filter().exclude(id=settings.ANONYMOUS_USER_ID).exclude(id__in=old_pm)
            if hasattr(self.request, "organization"):
                if self.request.organization:
                    users = users.filter(user_profile__organization=self.request.organization)
            self.fields['user'].queryset = users

    class Meta:
        fields = ['user']
        model = UserRole
        widgets = {
            'user': forms.Select(attrs={'class': 'selectize', 'data-url': reverse_lazy('role:user_add')}),
            'group': forms.HiddenInput(),
            'project': forms.HiddenInput()
        }


class SetProjectRoleForm(HTML5BootstrapModelForm, KOModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(SetProjectRoleForm, self).__init__(*args, **kwargs)
        self.fields['group'].empty_label = None
        role = kwargs.get('instance')
        if role is not None:
            old_admins = role.project.get_staffs_both_role
            old_admins.append(settings.ANONYMOUS_USER_ID)
            if hasattr(self.request, "organization"):
                if self.request.organization:
                    users = User.objects.filter(is_active=True, user_profile__organization=self.request.organization)\
                        .exclude(id__in=old_admins)
                else:
                    users = User.objects.filter(is_active=True).exclude(id__in=old_admins)
            else:
                users = User.objects.filter(is_active=True).exclude(id__in=old_admins)
            self.fields['user'].queryset = users
        self.fields['group'].queryset = Group.objects.filter(
            name__in=['Project Manager'])

    class Meta:
        fields = ['user', 'group','project']
        model = UserRole
        widgets = {
            'user': forms.Select(attrs={'class': 'selectize', 'data-url': reverse_lazy('role:user_add')}),
            'group': forms.Select(attrs={'class':'select', 'name': 'group', 'id':'value', 'onchange':'Hide()'}),
            'project': forms.HiddenInput()
        }


class ProjectForm(forms.ModelForm):
    x = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height = forms.FloatField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        is_new = kwargs.pop('new', None)
        org_id = kwargs.pop('organization_id', None)
        super(ProjectForm, self).__init__(*args, **kwargs)

        if not self.fields['location'].initial:
            self.fields['location'].initial = Point(85.3240, 27.7172, srid=4326)
        self.fields['type'].empty_label = None
        if self.instance.cluster_sites:
            self.fields.pop('cluster_sites')

        else:
            self.fields['cluster_sites'].label = "Do you want to cluster sites in this Project?"

        #self.fields['organization'].empty_label = None

        if not is_new:
            org_id = kwargs['instance'].organization.id
        self.fields['geo_layers'].queryset = GeoLayer.objects.filter(
            organization__id=org_id
        )

    class Meta:
        model = Project
        exclude = ('organization', 'is_active', 'site_meta_attributes',)
        #organization_filters = ['organization']
        widgets = {
            'is_active': forms.HiddenInput(),
            'address': forms.TextInput(),
            'location': forms.HiddenInput(),
            'logo': AdminImageWidget()
        }

    def save(self, commit=True, *args, **kwargs):
        is_new = kwargs.pop('new')
        
        if is_new:
            photo = super(ProjectForm, self).save(commit=False)
            photo.organization_id=kwargs.pop('organization_id')
            photo.save()
        
        photo = super(ProjectForm, self).save()

        x = self.cleaned_data.get('x')
        y = self.cleaned_data.get('y')
        w = self.cleaned_data.get('width')
        h = self.cleaned_data.get('height')

        if x is not None and y is not None:
            image = Image.open(photo.logo)
            cropped_image = image.crop((x, y, w+x, h+y))
            resized_image = cropped_image.resize((200, 200), Image.ANTIALIAS)
            # resized_image.save(photo.logo.path)
            resized_image_file = StringIO.StringIO()
            mime = mimetypes.guess_type(photo.logo.name)[0]
            plain_ext = mime.split('/')[1]
            resized_image.save(resized_image_file, plain_ext)
            default_storage.delete(photo.logo.name)
            default_storage.save(photo.logo.name, ContentFile(resized_image_file.getvalue()))
            resized_image_file.close()
        return photo

    def clean(self):
        lat = self.data.get("Longitude", "85.3240")
        long = self.data.get("Latitude", "27.7172")
        p = Point(round(float(lat), 6), round(float(long), 6),srid=4326)
        self.cleaned_data["location"] = p
        super(ProjectForm, self).clean()


class SiteForm(HTML5BootstrapModelForm, KOModelForm):
    x = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height = forms.FloatField(widget=forms.HiddenInput(), required=False)
    site_meta_attributes_ans = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        if not self.fields['location'].initial:
            self.fields['location'].initial = Point(85.3240, 27.7172,srid=4326)
        self.fields['logo'].label = "Image"
        self.fields['logo'].required = False

    class Meta:
        model = Site
        exclude = ('project', 'is_survey', 'is_active', 'region', 'current_status', 'current_progress',)
       
        project_filters = ['type']
        widgets = {
        'address': forms.TextInput(),
        # 'location': gform.OSMWidget(attrs={'map_width': 400, 'map_height': 400}),
        # 'project' : forms.HiddenInput(),
        'location': forms.HiddenInput(),
        'logo': AdminImageWidget()
        }



    def save(self, commit=True, *args, **kwargs):

        is_new = kwargs.pop('new')

        if is_new:
            photo = super(SiteForm, self).save(commit=False)
            photo.project_id = kwargs.pop('project_id')
            if 'region_id' in kwargs:
                photo.region_id = kwargs.pop('region_id')
            photo.save()

        photo = super(SiteForm, self).save()

        # if else for new  and update

        x = self.cleaned_data.get('x')
        y = self.cleaned_data.get('y')
        w = self.cleaned_data.get('width')
        h = self.cleaned_data.get('height')

        if x is not None and y is not None:
            image = Image.open(photo.logo)
            cropped_image = image.crop((x, y, w + x, h + y))
            resized_image = cropped_image.resize((200, 200), Image.ANTIALIAS)
            # resized_image.save(photo.logo.path)
            resized_image_file = StringIO.StringIO()
            mime = mimetypes.guess_type(photo.logo.name)[0]
            plain_ext = mime.split('/')[1]
            resized_image.save(resized_image_file, plain_ext)
            default_storage.delete(photo.logo.name)
            default_storage.save(photo.logo.name, ContentFile(resized_image_file.getvalue()))
            resized_image_file.close()
        return photo

    def clean(self):
        lat = self.data.get("Longitude")
        long = self.data.get("Latitude")
        p = Point(round(float(lat), 6), round(float(long), 6),srid=4326)
        self.cleaned_data["location"] = p
        super(SiteForm, self).clean()



class ProjectFormKo(HTML5BootstrapModelForm, KOModelForm):
    def __init__(self, *args, **kwargs):
        super(ProjectFormKo, self).__init__(*args, **kwargs)
        if not self.fields['location'].initial:
            self.fields['location'].initial = Point(85.3240, 27.7172,srid=4326)
        self.fields['type'].empty_label = None
        self.fields['organization'].empty_label = None
        self.fields['logo'].required = False

    class Meta:
        model = Project
        exclude = []
        widgets = {
        'address': forms.TextInput(),
        # 'location': gform.OSMWidget(attrs={'map_width': 400, 'map_height': 400}),
        'location': forms.HiddenInput(),
        'logo': AdminImageWidget()
        }

    def clean(self):
        lat = self.data.get("Longitude","85.3240")
        long = self.data.get("Latitude","27.7172")
        p = Point(round(float(lat), 6), round(float(long), 6),srid=4326)
        self.cleaned_data["location"] = p
        super(ProjectFormKo, self).clean()

my_default_errors = {
    'required': 'Excel File is required',
    'invalid': 'Upload a valid excel File'
}

class UploadFileForm(forms.Form):
    file = forms.FileField(error_messages=my_default_errors)


class BluePrintForm(forms.ModelForm):
    image = forms.FileField(label='File')

    class Meta:
        model = BluePrints
        fields = ('image', )


class RegionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RegionForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            idfs = self.instance.identifier.split('_')
            
            self.initial['identifier'] = idfs[len(idfs)-1]

    class Meta:
        model = Region
        exclude = ['project','date_created','date_updated', 'is_active', 'parent']

    def clean_identifier(self):
        identifier = self.cleaned_data['identifier']
        if "_" in identifier or " " in identifier:
            raise ValidationError("Identifier cannot contains '_' or ' ' , please try again by removing it.")
        return identifier


class SiteTypeForm(forms.ModelForm):
    class Meta:
        model = SiteType
        exclude = ('project','deleted')
        widgets = {
            'name': TextInput(attrs={'placeholder': 'name','id':'id_name', 'class':'form-control', }),
            'identifier': TextInput(attrs={'placeholder': 'ID', 'id':'id_identifier', 'class':'form-control', 'autocomplete': 'off','pattern':'[0-9]+', 'title':'Enter Positive numbers Only ', }),
        }



class SiteBulkEditForm(forms.Form):
    def __init__(self, project, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(SiteBulkEditForm, self).__init__(*args, **kwargs)

        self.fields['sites'] = forms.ModelMultipleChoiceField(
            widget=forms.CheckboxSelectMultiple,
            queryset=project.sites.filter(is_active=True),
        )

        for attr in project.site_meta_attributes:
            q_type = attr['question_type']
            q_name = attr['question_name']

            if q_type == 'Number':
                field = forms.FloatField()
            elif q_type == 'Date':
                field = forms.DateField()
            elif q_type == 'MCQ':
                options = attr.get('mcq_options') or []
                choices = [o.get('option_text') for o in options]
                choices = [(c, c) for c in choices]
                field = forms.ChoiceField(choices=choices)
            else:
                field = forms.CharField()

            self.fields[q_name] = field

