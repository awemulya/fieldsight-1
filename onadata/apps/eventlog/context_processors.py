from django.conf import settings

from onadata.apps.eventlog.models import FieldSightLog, FieldSightMessage


def events(request):
    from django.contrib.sites.models import Site
    site = Site.objects.first()
    if request.user.is_anonymous():
        messages = []
    else:
        messages = FieldSightMessage.inbox(request.user)
    oid = 0
    pid = 0
    sid = 0
    logs = []
    if request.group is not None:
        if request.group.name == "Super Admin":
           logs = FieldSightLog.objects.filter(is_seen=False)[:10]
           oid = 0
        elif request.group.name == "Organization Admin":
            logs = FieldSightLog.objects.filter(organization=request.organization).filter(is_seen=False)[:10]
            oid = request.organization.id
        elif request.group.name == "Project Manager":
            logs = FieldSightLog.objects.filter(organization=request.organization).filter(is_seen=False)[:10]
            if request.project:
                pid = request.project.id
        elif request.group.name in ["Reviewer", "Site Supervisor"]:
            logs = FieldSightLog.objects.filter(organization=request.organization).filter(is_seen=False)[:10]
            if request.site:
                sid = request.site.id
    else:
        logs = []
        oid = None
    channels_url = settings.WEBSOCKET_URL+":"+settings.WEBSOCKET_PORT+"/" \
    if settings.WEBSOCKET_PORT else settings.WEBSOCKET_URL+"/"
    return {
        'notifications': logs,
        'fieldsight_message': messages,
        'oid': oid,
        'pid': pid,
        'sid': sid,
        'channels_url': channels_url,
        'site_name': site.domain

    }