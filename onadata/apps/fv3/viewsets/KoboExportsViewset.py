import os

from django.core.files.storage import get_storage_class, FileSystemStorage
from django.http import HttpResponseRedirect
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from onadata.apps.fsforms.enketo_utils import CsrfExemptSessionAuthentication
from rest_framework.response import Response
from django.utils.translation import ugettext as _
from onadata.apps.fsforms.models import FieldSightXF
from onadata.apps.fv3.serializers.KoboExportSerializer import ExportSerializer
from onadata.apps.viewer.models import Export
from onadata.apps.viewer.tasks import create_async_export
from onadata.libs.utils.logger_tools import response_with_mimetype_and_name
from onadata.libs.utils.viewer_tools import export_def_from_filename


class ExportViewSet(viewsets.ModelViewSet):
    queryset = Export.objects.all()
    serializer_class = ExportSerializer
    authentication_classes = [CsrfExemptSessionAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        params = self.request.query_params
        id = params.get('id')
        fsxf = params.get('fsxf')
        is_project = params.get('is_project')
        version = params.get('version')
        if not (id and fsxf and is_project):
            return []
        if is_project in ["1", True, 1]:
            self.queryset = self.queryset.filter(fsxf=fsxf)
        else:
            self.queryset = self.queryset.filter(fsxf=fsxf, site=id)
        if version:
            return self.queryset.filter(version=version)
        return self.queryset

    def create(self, request, *args, **kwargs):
        params = self.request.query_params
        id = params.get('id')
        fsxf = params.get('fsxf')
        is_project = params.get('is_project')
        version = params.get('version', 0)
        if not (id and fsxf and is_project):
            return Response({'error': 'Parameters missing'}, status=status.HTTP_400_BAD_REQUEST)
        fsxf = FieldSightXF.objects.get(pk=fsxf)
        if is_project == 1 or is_project == '1':
            site_id = None
            query = {"fs_project_uuid": str(fsxf.id)}
        else:
            site_id = id
            if fsxf.site:
                query = {"fs_uuid": str(fsxf.id)}
            else:
                query = {"fs_project_uuid": str(fsxf.id), "fs_site": site_id}
        force_xlsx = True
        if version not in ["0", 0]:
            query["__version__"] = version
        deleted_at_query = {
            "$or": [{"_deleted_at": {"$exists": False}},
                    {"_deleted_at": None}]
        }
        # join existing query with deleted_at_query on an $and
        query = {"$and": [query, deleted_at_query]}
        print("query at excel generation", query)

        # export options
        group_delimiter = request.POST.get("group_delimiter", '/')
        if group_delimiter not in ['.', '/']:
            return Response({'error': _("%s is not a valid delimiter" % group_delimiter)}, status=status.HTTP_400_BAD_REQUEST)

        # default is True, so when dont_.. is yes
        # split_select_multiples becomes False
        split_select_multiples = request.POST.get(
            "dont_split_select_multiples", "no") == "no"

        binary_select_multiples = False
        # external export option
        meta = request.POST.get("meta")
        options = {
            'group_delimiter': group_delimiter,
            'split_select_multiples': split_select_multiples,
            'binary_select_multiples': binary_select_multiples,
            'meta': meta.replace(",", "") if meta else None
        }

        create_async_export(fsxf.xf, 'xls', query, force_xlsx, options, is_project, fsxf.id, site_id, version, False)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        export = self.get_object()
        ext, mime_type = export_def_from_filename(export.filename)
        default_storage = get_storage_class()()
        if not isinstance(default_storage, FileSystemStorage):
            return HttpResponseRedirect(default_storage.url(export.filepath))
        basename = os.path.splitext(export.filename)[0]
        response = response_with_mimetype_and_name(
            mime_type, name=basename, extension=ext,
            file_path=export.filepath, show_date=False)
        return response

