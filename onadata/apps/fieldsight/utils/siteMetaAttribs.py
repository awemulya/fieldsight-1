import json

from django.db import connection
from django.db.models import Value

from onadata.apps.fieldsight.models import Site
from onadata.apps.fsforms.models import FieldSightXF

"""
This module is used to get the site meta attributes answers of a specified site.
The site meta attributes answers that are to be selected from forms are not directly stored in the database.
To remove the overhead computation of calculating such answers repeatedly, it would be a lot easier if they are saved 
in the database directly. 

To be used in the future this module provides site meta attributes answers in a format to be saved in the database directly.
"""


def find_answer_from_dict(sub_answers={}, question_name=""):
    answer = sub_answers.get(question_name, '')
    if not answer:
        for k, v in sub_answers.items():
            if isinstance(v, list) and len(v) and isinstance(v[0], dict):
                return find_answer_from_dict(v[0], question_name)
    return answer

def get_form_answer(site_id, meta):
    fxf = FieldSightXF.objects.filter(pk=int(meta.get('form_id', "0")))
    if fxf:
        sub = fxf[0].project_form_instances.filter(site_id=site_id).order_by('-instance_id')[:1]
        if sub:
            if meta['question']['type'] == 'repeat':
                return ""

            sub_answers = sub[0].instance.json
            if meta['question']['type'] == "repeat":
                answer = ""
            else:
                answer = find_answer_from_dict(sub_answers, meta.get('question').get('name'))

            if meta['question']['type'] in ['photo', 'video', 'audio'] and answer is not "":
                answer = 'http://app.fieldsight.org/attachment/medium?media_file=' + fxf[0].xf.user.username + '/attachments/' + answer
        else:
            answer = ""
    else:
        answer = ""
    return answer


def get_form_sub_status(site_id, meta):
    fxf = FieldSightXF.objects.filter(pk=int(meta.get('form_id', "0")))
    if fxf:
        sub_date = fxf[0].project_form_instances.filter(site_id=site_id).order_by('-instance_id').values('date')[:1]
        if sub_date:
            answer = "Last submitted on " + sub_date[0]['date'].strftime("%d %b %Y %I:%M %P")
        else:
            answer = ""
    else:
        answer = ""
    return answer


def get_form_ques_ans_status(site_id, meta):
    fxf = FieldSightXF.objects.filter(pk=int(meta.get('form_id', "0")))
    if fxf:
        sub = fxf[0].project_form_instances.filter(site_id=site_id).order_by('-instance_id')[:1]
        if sub:

            sub_answers = sub[0].instance.json
            get_answer = sub_answers.get(meta.get('question').get('name'), None)

            if get_answer:
                answer = "Answered"
            else:
                answer = ""

        else:
            answer = ""
    else:
        answer = ""
    return answer


def get_form_submission_count(site_id, meta):
    fxf = FieldSightXF.objects.filter(pk=int(meta.get('form_id', "0")))
    if fxf:
        answer = fxf[0].project_form_instances.filter(site_id=site_id).count()
    else:
        # answer = "No Form"
        answer = ""
    return answer


def get_site_meta_ans(site_id):
    metas = {}
    site = Site.objects.get(pk=site_id)
    project = site.project
    main_project = project.id

    def generate_ans(metas, project_id, metas_to_parse, meta_answer, parent_selected_metas, project_metas):

        for meta in metas_to_parse:
            # if project_metas and meta not in project_metas:
            #     continue
            if meta.get('question_type') == "Link":
                if parent_selected_metas:
                    selected_metas = parent_selected_metas
                else:
                    selected_metas = meta.get('metas')
                if meta.get('project_id') == main_project:
                    continue
                referenced_site = Site.objects.filter(identifier=meta_answer.get(meta.get('question_name'), None),
                                              project_id=meta.get('project_id'))
                if referenced_site and str(referenced_site[0].project_id) in selected_metas:
                    answer = meta_answer.get(meta.get('question_name'))
                    sub_metas = {}
                    generate_ans(sub_metas,
                                 referenced_site[0].project_id,
                                 selected_metas[str(referenced_site[0].project_id)],
                                 referenced_site[0].site_meta_attributes_ans,
                                 selected_metas,
                                 referenced_site[0].project.site_meta_attributes)
                    metas[meta.get('question_name')] = {"children": sub_metas, "answer": answer}

                else:
                    answer = "No site referenced"
                    metas[meta.get('question_name')] = answer

            else:
                if meta.get('question_type') == "Form":
                    answer = get_form_answer(site_id, meta)

                elif meta.get('question_type') == "FormSubStat":
                    answer = get_form_sub_status(site_id, meta)

                elif meta.get('question_type') == "FormQuestionAnswerStatus":
                    answer = get_form_ques_ans_status(site_id, meta)

                elif meta.get('question_type') == "FormSubCountQuestion":
                    answer = get_form_submission_count(site_id, meta)

                else:
                    answer = meta_answer.get(meta.get('question_name'), "")
                metas[meta.get('question_name')] = answer

    generate_ans(metas, project.id, project.site_meta_attributes, site.site_meta_attributes_ans, None, None)

    return metas


def get_meta_ans(site, meta_attr):
    data = {}

    def generate_ans(metas, project_id, metas_to_parse, meta_answer, parent_selected_metas, project_metas):

        for meta in metas_to_parse:
            # if project_metas and meta not in project_metas:
            #     continue
            if meta.get('question_type') == "Link":
                if parent_selected_metas:
                    selected_metas = parent_selected_metas
                else:
                    selected_metas = meta.get('metas')
                main_project = site.project_id
                if meta.get('project_id') == main_project:
                    continue
                referenced_site = Site.objects.filter(identifier=meta_answer.get(meta.get('question_name'), None),
                                              project_id=meta.get('project_id'))
                if referenced_site and str(referenced_site[0].project_id) in selected_metas:
                    answer = meta_answer.get(meta.get('question_name'))
                    sub_metas = {}
                    generate_ans(sub_metas,
                                 referenced_site[0].project_id,
                                 selected_metas[str(referenced_site[0].project_id)],
                                 referenced_site[0].all_ma_ans,
                                 selected_metas,
                                 referenced_site[0].project.site_meta_attributes)
                    metas[meta.get('question_name')] = {"children": sub_metas, "answer": answer}

                else:
                    answer = "No site referenced"
                    metas[meta.get('question_name')] = answer

            else:
                site_id = site.id
                if meta.get('question_type') == "Form":
                    answer = get_form_answer(site_id, meta)

                elif meta.get('question_type') == "FormSubStat":
                    answer = get_form_sub_status(site_id, meta)

                elif meta.get('question_type') == "FormQuestionAnswerStatus":
                    answer = get_form_ques_ans_status(site_id, meta)

                elif meta.get('question_type') == "FormSubCountQuestion":
                    answer = get_form_submission_count(site_id, meta)

                else:
                    answer = meta_answer.get(meta.get('question_name'), "")
                metas[meta.get('question_name')] = answer

    generate_ans(data, None, [meta_attr], site.all_ma_ans, None, None)

    return data


def update_site_meta_ans(site, deleted_metas, changed_metas):
    if deleted_metas:
        for m in deleted_metas:
            site.all_ma_ans.pop(m['question_name'])
            site.site_meta_attributes_ans.pop(m['question_name'])
    if changed_metas:
        for m in changed_metas:
            meta = get_meta_ans(site, m)
            site.all_ma_ans.update(meta)
    site.save()


def bulk_update_sites_all_logos(site_dict):
    from django.db.models import Case, When

    Site.objects.filter(
        pk__in=site_dict
    ).update(
        logo=Case(*[When(pk=entry_pk, then=Value(logo))
                        for entry_pk, logo in site_dict.items()]))


def bulk_upload_json_site_all_ma(sites):
    if not sites:
        return
    pk_list = [str(s.id) for s in sites]
    pk_list_string = ','.join(pk_list)
    whens = ""
    for s in sites:
        when_statement = "WHEN id={0} THEN CAST('{1}' as json) ".format(s.id, json.dumps(s.all_ma_ans))
        whens += when_statement
    statement = "UPDATE fieldsight_site set all_ma_ans = CASE "
    where = " END WHERE id IN (" + pk_list_string + ")"
    query = statement + whens + where

    with connection.cursor() as cursor:
        cursor.execute(query)


def bulk_update_sites_all_location(sites):
    if not sites:
        return
    pk_list = [str(s.id) for s in sites]
    pk_list_string = ','.join(pk_list)
    whens = ""
    for s in sites:
        when_statement = "WHEN id={0} THEN ST_SetSRID(ST_MakePoint({1},{2}),4326) ".format(s.id, s.location.x, s.location.y)
        whens += when_statement
    statement = "UPDATE fieldsight_site set location = CASE "
    where = " END WHERE id IN (" + pk_list_string + ")"
    query = statement + whens + where

    with connection.cursor() as cursor:
        cursor.execute(query)

