from django.conf.urls import url, include

from rest_framework import routers
from onadata.apps.fv3.viewsets.ProjectDashboardViewSet import ProjectDashboardViewSet, ProjectProgressTableViewSet, \
    project_regions_types, ProjectSurveyFormsViewSet, SiteFormViewSet, SitelistForMetasLink

router = routers.DefaultRouter()

router.register(r'site-form', SiteFormViewSet, base_name='site_form')

project_dashboard_urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api/project/(?P<pk>\d+)/$', ProjectDashboardViewSet.as_view({'get': 'retrieve'}), name='project'),
    url(r'^api/project-regions-types/(?P<pk>\d+)/$', project_regions_types, name='project_regions_types'),
    url(r'^api/progress-table/(?P<pk>\d+)/$', ProjectProgressTableViewSet.as_view(),
        name='progress_table'),
    url(r'^api/project-survey-forms/(?P<pk>\d+)/$', ProjectSurveyFormsViewSet.as_view(),
        name='project_survey_forms'),
    url(r'^api/project-sites-metas/(?P<pk>\d+)/$', SitelistForMetasLink.as_view({'get': 'list'}),
        name='project_sites_metas'),

]


