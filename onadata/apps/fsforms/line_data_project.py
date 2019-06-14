import datetime
from collections import OrderedDict
strptime = datetime.datetime.strptime
from django.db.models import Count

from .models import FInstance

def date_range(start, end, intv):
    start = strptime(start,"%Y%m%d")
    end = strptime(end,"%Y%m%d")
    diff = (end  - start ) / intv
    for i in range(intv):
        yield (start + diff * i)
    yield end


class LineChartGenerator(object):

    def __init__(self, project):
        self.project = project
        self.date_list = list(date_range(project.date_created.strftime("%Y%m%d"), datetime.datetime.today().strftime("%Y%m%d"), 6))

    def get_count(self, date):
        date = date + datetime.timedelta(days=1)
        return self.project.project_instances.filter(date__lte=date.date()).count()

    def data(self):
        d = OrderedDict()
        dt = self.date_list
        for date in dt:
            count = self.get_count(date)
            d[date.strftime('%Y-%m-%d')] = count
        return d


class LineChartGeneratorProject(object):

    def __init__(self, project):
        self.project = project
        self.date_list = list(date_range(project.date_created.strftime("%Y%m%d"), datetime.datetime.today().strftime("%Y%m%d"), 6))

    def get_count(self, date):
        date = date + datetime.timedelta(days=1)
        return self.project.project_instances.filter(date__lte=date.date()).count()

    def data(self):
        d = OrderedDict()
        dt = self.date_list
        for date in dt:
            count = self.get_count(date)
            d[date.strftime('%Y-%m-%d')] = count
        return d


class LineChartGeneratorOrganization(object):

    def __init__(self, organization):
        self.organization = organization
        self.date_list = list(date_range(organization.date_created.strftime("%Y%m%d"), datetime.datetime.today().strftime("%Y%m%d"), 6))

    def get_count(self, date):
        date = date + datetime.timedelta(days=1)
        return FInstance.objects.filter(project__organization=self.organization, date__lte=date.date()).count()

    def data(self):
        d = OrderedDict()
        dt = self.date_list
        for date in dt:
            count = self.get_count(date)
            d[date.strftime('%Y-%m-%d')] = count
        return d


class LineChartGeneratorSite(object):

    def __init__(self, site):
        self.site = site
        self.date_list = list(date_range(site.date_created.strftime("%Y%m%d"), datetime.datetime.today().strftime("%Y%m%d"), 6))

    def get_count(self, date):
        date = date + datetime.timedelta(days=1)
        return self.site.site_instances.filter(date__lte=date.date()).count()

    def data(self):
        d = OrderedDict()
        dt = self.date_list
        for date in dt:
            count = self.get_count(date)
            d[date.strftime('%Y-%m-%d')] = count
        return d


class ProgressGeneratorSite(object):

    def __init__(self, site):
        self.site = site

    def data(self):
        d = OrderedDict()
        main_stages_site = self.site.stages.filter(stage__isnull=True)
        for ms in main_stages_site:
            sub_stages = ms.parent.filter(stage_forms__isnull=False)
            for sub_stage in sub_stages:
                try:
                    fsform = sub_stage.stage_forms
                    approved_submission = fsform.site_form_instances.filter().order_by("-date").first()
                    if approved_submission.form_status == 3:
                        d[ms.order + sub_stage.order * 0.1] = approved_submission.date.strftime('%Y-%m-%d')
                except:
                    pass
        main_stages_project = self.site.project.stages.filter(stage__isnull=True)
        for ms in main_stages_project:
            sub_stages = ms.parent.filter(stage_forms__isnull=False)
            for sub_stage in sub_stages:
                try:
                    fsform = sub_stage.stage_forms
                    approved_submission = fsform.project_form_instances.filter(site_id=self.site.id).order_by("-date").first()
                    if approved_submission.form_status == 3:
                        d[ms.order + sub_stage.order * 0.1] = approved_submission.date.strftime('%Y-%m-%d')
                except:
                    pass
        return d


