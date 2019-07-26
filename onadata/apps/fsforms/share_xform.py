from guardian.shortcuts import assign_perm, get_users_with_perms
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
import time


def share_m2m(users, forms):
    for user in users:
        for xform in forms:
            if not user.has_perm('change_xform', xform):
                assign_perm('change_xform', user, xform)
            if not user.has_perm('change_xform', xform):
                assign_perm('view_xform', user, xform)


# module to share multiple forms to a single user
def share_forms(user, forms):
    from onadata.apps.fsforms.models import ObjectPermission, Asset
    for fxf in forms:
        time.sleep(1)
        codenames = ['view_asset', 'change_asset']  # specific permissions to view and edit the form
        permissions = Permission.objects.filter(content_type__app_label='kpi', codename__in=codenames)
        for perm in permissions:
            object_id = Asset.objects.get(uid=fxf.xf.id_string).id

            # ASSET_CONTENT_TYPE_ID should be included in the local_settings. It can be generated by:
            # ContentType.objects.get(app_label='kpi', model='asset').id
            content_type = ContentType.objects.get(id=settings.ASSET_CONTENT_TYPE_ID)

            # Create the new permission if specified permission for the user does not exist in the form
            if not ObjectPermission.objects.filter(object_id=object_id,
                                               content_type=content_type,
                                               user=user,
                                               permission_id=perm.pk).exists():
                ObjectPermission.objects.create(
                    object_id=object_id,
                    content_type=content_type,
                    user=user,
                    permission_id=perm.pk,
                    deny=False,
                    inherited=False
                )
            else:
                continue

    return True


# module to share a single form to multiple users
def share_form(users, xform):
    from onadata.apps.fsforms.models import ObjectPermission, Asset
    for user in users:
        time.sleep(1)
        codenames = ['view_asset', 'change_asset']
        permissions = Permission.objects.filter(content_type__app_label='kpi', codename__in=codenames)
        for perm in permissions:
            object_id = Asset.objects.get(uid=xform.id_string).id

            content_type = ContentType.objects.get(id=settings.ASSET_CONTENT_TYPE_ID)

            # Create the new permission
            if not ObjectPermission.objects.filter(object_id=object_id,
                                                   content_type=content_type,
                                                   user=user,
                                                   permission_id=perm.pk).exists():
                ObjectPermission.objects.create(
                    object_id=object_id,
                    content_type=content_type,
                    user=user,
                    permission_id=perm.pk,
                    deny=False,
                    inherited=False
                )
            else:
                continue

    return True


# share form globally
# setting view and edit permissions on the forms to anonymous user makes the form to be shared globally
def share_form_global(form):
    from onadata.apps.fsforms.models import ObjectPermission, Asset, SharedFieldSightForm
    codenames = ['view_asset', 'view_submissions']
    permissions = Permission.objects.filter(content_type__app_label='kpi', codename__in=codenames)
    for perm in permissions:
        object_id = Asset.objects.get(uid=form.id_string).id
        content_type = ContentType.objects.get(id=settings.ASSET_CONTENT_TYPE_ID)
        user = User.objects.get(id=-1)
        if not ObjectPermission.objects.filter(
            object_id=object_id,
            content_type=content_type,
            user=user,
            permission_id=perm.pk,
            deny=False,
            inherited=False).exists():
            ObjectPermission.objects.create(
                object_id=object_id,
                content_type=content_type,
                user=user,
                permission_id=perm.pk,
                deny=False,
                inherited=False)

            shared, created = SharedFieldSightForm.objects.get_or_create(xf=form, shared=True)
            if not created:
                SharedFieldSightForm.objects.filter(xf=form).update(shared=True)

        else:
            continue
    return True


def share_o2o(user, xform):
    if not user.has_perm('change_xform', xform):
        assign_perm('change_xform', user, xform)
    if not user.has_perm('view_xform', xform):
        assign_perm('view_xform', user, xform)


def shared_users(xform):
    return get_users_with_perms(xform)
