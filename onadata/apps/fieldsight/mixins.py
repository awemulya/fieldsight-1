from functools import wraps

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.http import JsonResponse
from django.views.generic.edit import UpdateView as BaseUpdateView, CreateView as BaseCreateView, DeleteView as BaseDeleteView
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from onadata.apps.fieldsight.models import Organization, Project, Site
from onadata.apps.users.models import UserProfile
from .helpers import json_from_object


class DeleteView(BaseDeleteView):
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = super(DeleteView, self).post(request, *args, **kwargs)
        # messages.success(request, ('%s %s' % (self.object.__class__._meta.verbose_name.title(), _('successfully deleted!'))))
        return response


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)


class OrganizationOrProjectRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.organization and not request.project:
            raise PermissionDenied()
        if hasattr(self, 'check'):
            if not getattr(request.organization, self.check)() or not getattr(request.organization, self.check)():
                raise PermissionDenied()
        return super(OrganizationOrProjectRequiredMixin, self).dispatch(request, *args, **kwargs)


class OrganizationRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.organization:
            raise PermissionDenied()
        if hasattr(self, 'check'):
            if not getattr(request.organization, self.check)():
                raise PermissionDenied()
        return super(OrganizationRequiredMixin, self).dispatch(request, *args, **kwargs)


class ProjectRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.project:
            raise PermissionDenied()
        if hasattr(self, 'check'):
            if not getattr(request.project, self.check)():
                raise PermissionDenied()
        return super(ProjectRequiredMixin, self).dispatch(request, *args, **kwargs)


class SiteRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.site:
            raise PermissionDenied()
        if hasattr(self, 'check'):
            if not getattr(request.project, self.check)():
                raise PermissionDenied()
        return super(SiteRequiredMixin, self).dispatch(request, *args, **kwargs)


class UpdateView(BaseUpdateView):
    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['scenario'] = _('Edit')
        context['base_template'] = 'base.html'
        super(UpdateView, self).get_context_data()
        return context


class CreateView(BaseCreateView):
    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['scenario'] = _('Add')
        if self.request.is_ajax():
            base_template = 'fieldsight/fieldsight_modal.html'
        else:
            base_template = 'fieldsight/fieldsight_base.html'
        context['base_template'] = base_template
        return context


class AjaxableResponseMixin(object):
    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            if 'ret' in self.request.GET:
                obj = getattr(self.object, self.request.GET['ret'])
            else:
                obj = self.object
            return json_from_object(obj)
        else:
            return response


class AjaxableResponseMixinUser(object):
    def form_invalid(self, form):
        response = super(AjaxableResponseMixinUser, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        response = super(AjaxableResponseMixinUser, self).form_valid(form)
        if self.request.is_ajax():
            if 'ret' in self.request.GET:
                obj = getattr(self.object, self.request.GET['ret'])
            else:
                obj = self.object
            if isinstance(obj, User):
                obj.set_password(form.cleaned_data['password'])
                obj.is_superuser = True
                obj.save()
                org = None
                if hasattr(self.request, "organization"):
                    if self.request.organization:
                        org = self.request.organization
                if not org:
                    organization = int(form.cleaned_data['organization'])
                    org = Organization.objects.get(pk=organization)
                user_profile, created = UserProfile.objects.get_or_create(user=obj, organization=org)
            return json_from_object(obj)
        else:
            return response


class TableObjectMixin(TemplateView):
    def get_context_data(self, *args, **kwargs):
        context = super(TableObjectMixin, self).get_context_data(**kwargs)
        if self.kwargs:
            pk = int(self.kwargs.get('pk'))
            obj = get_object_or_404(self.model, pk=pk, company=self.request.company)
            scenario = 'Update'
        else:
            obj = self.model(company=self.request.company)
            # if obj.__class__.__name__ == 'PurchaseVoucher':
            #     tax = self.request.company.settings.purchase_default_tax_application_type
            #     tax_scheme = self.request.company.settings.purchase_default_tax_scheme
            #     if tax:
            #         obj.tax = tax
            #     if tax_scheme:
            #         obj.tax_scheme = tax_scheme
            scenario = 'Create'
        data = self.serializer_class(obj).data
        context['data'] = data
        context['scenario'] = scenario
        context['obj'] = obj
        return context


class TableObject(object):
    def get_context_data(self, *args, **kwargs):
        context = super(TableObject, self).get_context_data(**kwargs)
        if self.kwargs:
            pk = int(self.kwargs.get('pk'))
            obj = get_object_or_404(self.model, pk=pk, company=self.request.company)
            scenario = 'Update'
        else:
            obj = self.model(company=self.request.company)
            # if obj.__class__.__name__ == 'PurchaseVoucher':
            #     tax = self.request.company.settings.purchase_default_tax_application_type
            #     tax_scheme = self.request.company.settings.purchase_default_tax_scheme
            #     if tax:
            #         obj.tax = tax
            #     if tax_scheme:
            #         obj.tax_scheme = tax_scheme
            scenario = 'Create'
        data = self.serializer_class(obj).data
        context['data'] = data
        context['scenario'] = scenario
        context['obj'] = obj
        return context


class OrganizationView(LoginRequiredMixin):
    def form_valid(self, form):
        if self.request.organization:
            form.instance.organization = self.request.organization
        return super(OrganizationView, self).form_valid(form)

    def get_queryset(self):
        if self.request.organization:
            return super(OrganizationView, self).get_queryset().filter(organization=self.request.organization)
        else:
            return super(OrganizationView, self).get_queryset()

    def get_form(self, *args, **kwargs):
        form = super(OrganizationView, self).get_form(*args, **kwargs)
        if self.request.organization:
            form.organization = self.request.organization
            if hasattr(form.Meta, 'organization_filters'):
                for field in form.Meta.organization_filters:
                    form.fields[field].queryset = Organization.objects.filter(id=self.request.organization.pk)
        return form


class OrganizationViewFromProfile(object):
    model = User
    success_url = reverse_lazy('fieldsight:user-list')

    def get_queryset(self):
        if self.request.organization:
            return super(OrganizationViewFromProfile, self).get_queryset().\
                filter(user_profile__organization=self.request.organization)
        else:
            return super(OrganizationViewFromProfile, self).get_queryset().filter(pk__gt=0)


class ProjectView(LoginRequiredMixin):
    def form_valid(self, form):
        if self.request.project:
            form.instance.project = self.request.project
        return super(ProjectView, self).form_valid(form)

    def get_queryset(self):
        if self.request.project:
            return super(ProjectView, self).get_queryset().filter(project=self.request.project)
        elif self.request.organization:
            return super(ProjectView, self).get_queryset().filter(project__organization=self.request.organization)
        else:
            return super(ProjectView, self).get_queryset()
            
    def get_form(self, *args, **kwargs):
        form = super(ProjectView, self).get_form(*args, **kwargs)
        if self.request.project:
            form.project = self.request.project
        if hasattr(form.Meta, 'project_filters'):
            for field in form.Meta.project_filters:
                if self.request.project:
                    form.fields[field].queryset = Project.objects.filter(id=self.request.project.pk)
                elif self.request.organization:
                    form.fields[field].queryset = Project.objects.filter(organization=self.request.organization)
        return form


class SiteView(SiteRequiredMixin):
    def form_valid(self, form):
        form.instance.site = self.request.site
        return super(SiteView, self).form_valid(form)

    def get_queryset(self):
        return super(SiteView, self).get_queryset().filter(site=self.request.site)

    def get_form(self, *args, **kwargs):
        form = super(SiteView, self).get_form(*args, **kwargs)
        form.site = self.request.site
        if hasattr(form.Meta, 'site_filters'):
            for field in form.Meta.site_filters:
                form.fields[field].queryset = form.fields[field].queryset.filter(site=form.site)
        if hasattr(form.Meta, 'project_filters'):
            for field in form.Meta.project_filters:
                form.fields[field].queryset = form.fields[field].queryset.filter(project=form.site.project)
        return form


class ProfileView(LoginRequiredMixin):
    def form_valid(self, form):
        if self.request.user:
            form.instance.user = self.request.user
        return super(ProfileView, self).form_valid(form)

    def get_form(self, *args, **kwargs):
        form = super(ProfileView, self).get_form(*args, **kwargs)
        if self.request.user:
            form.fields['first_name'].initial = self.request.user.first_name
            form.fields['last_name'].initial = self.request.user.last_name
        return form


USURPERS = {
    # central engineer to project , same on roles.
    'Site': ['Reviewer', 'Site Supervisor', 'Project Manager', 'Reviewer',
             'Organization Admin', 'Super Admin'],
    'KoboForms': ['Project Manager', 'Reviewer', 'Organization Admin', 'Super Admin'],
    'Project': ['Project Manager', 'Organization Admin', 'Super Admin',],
    'Reviewer': ['Project Manager', 'Reviewer', 'Organization Admin', 'Super Admin'],
    'Organization': ['Organization Admin', 'Super Admin'],
    'admin': ['Super Admin'],
}


class OwnerMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            pk = kwargs.get('pk')
            profile = UserProfile.objects.get(pk=pk)
            if request.user == profile.user:
                return super(OwnerMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class SiteMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if request.role.group.name in USURPERS['Site']:
                return super(SiteMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class ProjectMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if request.role.group.name in USURPERS['Project']:
                return super(ProjectMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class ReviewerMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if request.is_super_admin:
                return super(ReviewerMixin, self).dispatch(request, *args, **kwargs)
            # elif request.group.name == "Organization Admin":
            #     pk = self.kwargs.get('pk', False)
            #     if not pk:
            #         return super(ReviewerMixin, self).dispatch(request, *args, **kwargs)
            #     else:
            #         site = Site.objects.get(pk=pk)
            #         organization = site.project.organization
            #         if organization == request.organization:
            #             return super(ReviewerMixin, self).dispatch(request, *args, **kwargs)
            # elif request.role.group.name in USURPERS['Reviewer']:
            #     pk = self.kwargs.get('pk', False)
            #     if not pk:
            #         return super(ReviewerMixin, self).dispatch(request, *args, **kwargs)
            #     else:
            #         site = Site.objects.get(pk=pk)
            #         if site.project == request.project:
            #             return super(ReviewerMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class KoboFormsMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if request.role.group.name in USURPERS['KoboForms']:
                return super(KoboFormsMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


#use in view class
class OrganizationMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if request.role.group.name in USURPERS['Organization']:
                return super(OrganizationMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class MyOwnOrganizationMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if request.role.group.name in ['Super Admin']:
                return super(MyOwnOrganizationMixin, self).dispatch(request, *args, **kwargs)
            if request.role.group.name in ['Organization Admin']:
                if request.role.organization.pk == int(self.kwargs.get('pk','0')):
                    return super(MyOwnOrganizationMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class MyOwnProjectMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if request.role.group.name in ['Super Admin']:
                return super(MyOwnProjectMixin, self).dispatch(request, *args, **kwargs)
            if request.role.group.name in ['Organization Admin']:
                if request.role.organization == Project.objects.get(pk=kwargs.get('pk', 0)).organization:
                    return super(MyOwnProjectMixin, self).dispatch(request, *args, **kwargs)
            if request.role.group.name in ['Reviewer', 'Project Manager']:
                if request.role.project.pk == int(self.kwargs.get('pk', '0')):
                    return super(MyOwnProjectMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class SuperAdminMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if request.role.group.name in USURPERS['admin']:
                return super(SuperAdminMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


# use in all view functions
def group_required(group_name):
    def _check_group(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated():
                if request.role.group.name in USURPERS.get(group_name, []):
                    return view_func(request, *args, **kwargs)
            raise PermissionDenied()
        return wrapper
    return _check_group