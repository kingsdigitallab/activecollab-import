#!/usr/bin/env python

import os
import time

import requests

import activecollab as ac
import simplejson
from dateutil.parser import parse

AC_DEFAULT_USER = 32

ac_users = ac.get_activecollabusers()

JIRA_BASE_URL = 'https://jira.dighum.kcl.ac.uk/rest/api/latest/'
JIRA_SEARCH_URL = JIRA_BASE_URL + 'search/'

jira_projects = {}

with open('jira_projects_to_import.json') as f:
    jira_projects = simplejson.loads(f.read())


def main():
    with open('jira_secrets.json.nogit') as f:
        secrets = simplejson.loads(f.read())

    jira_auth = (secrets['username'], secrets['password'])

    for jira_project_key in jira_projects:
        ac_project_id = jira_projects[jira_project_key]

        print(jira_project_key)

        params = {
            'jql': 'project={}'.format(jira_project_key),
            'maxResults': '-1',
            'fields': ['self']
        }

        r = requests.get(JIRA_SEARCH_URL, auth=jira_auth, params=params)

        if r.status_code == 200:
            issues = r.json()['issues']

            tasklists = ac.get_activecollab_tasklists(ac_project_id)

            for issue in issues:
                import_issue(issue, jira_auth, ac_project_id, tasklists)

        else:
            print('Failed to get issues for {} project'.format(
                jira_project_key))

        print()


def import_issue(issue, jira_auth, ac_project_id, tasklists):
    url = issue['self']

    issue_r = requests.get(url, auth=jira_auth)

    if issue_r.status_code == 200:
        details = issue_r.json()
        fields = details['fields']
        labels = []

        key = details['key']
        summary = fields['summary']

        try:
            task_name = '{}: {}'.format(key, summary)[:150]
        except:
            # Invalid character in
            task_name = summary[:150]

        print(task_name)

        label = get_label_for_issue_type(fields['issuetype']['name'])
        if label:
            labels.append(label)

        description = fields['description']

        priority = fields['priority']['name']
        label = get_label_for_priority(priority)
        if label:
            labels.append(label)

        status = fields['status']['name']

        list_name = get_list_for_status(status)
        list_id = tasklists[list_name]

        label = get_label_for_status(status)
        if label:
            labels.append(label)

        if fields['resolution']:
            label = get_label_for_resolution(fields['resolution']['name'])
            if label:
                labels.append(label)

        assignee = get_activecollab_user(fields['assignee'])
        updated = convert_date_to_timestamp(fields['updated'])

        payload = {
            'name': task_name,
            'assignee_id': assignee,
            'body': description,
            'created_by_id': get_activecollab_user(fields['reporter']),
            'labels': labels,
            'task_list_id': list_id,
            'is_important': is_important(priority),
        }

        completed = is_completed(status)

        if completed:
            payload['is_completed'] = completed
            payload['completed_by_id'] = assignee
            payload['completed_on'] = updated

        r = ac.post_activecollab(
            'projects/{}/tasks'.format(ac_project_id), params=payload)

        if r and 'single' in r and 'id' in r['single']:
            task_id = r['single']['id']

            # updates the date fields of the task with the dates from jira
            created = convert_date_to_timestamp(fields['created'])
            ac.put_activecollab(
                'projects/{}/tasks/{}'.format(ac_project_id, task_id),
                {'created_on': created})
            ac.put_activecollab(
                'projects/{}/tasks/{}'.format(ac_project_id, task_id),
                {'updated_on': updated})

            # comments
            import_comments(task_id, fields)

            # attachments
            import_attachments(ac_project_id, task_id, fields, jira_auth)
        else:
            print('Failed to create task for issue {}'.format(task_name))
            print(r)
    else:
        print('Failed to get issue {}'.format(url))


def import_comments(task_id, fields):
    if 'comment' in fields and 'comments' in fields['comment']:
        comments = fields['comment']['comments']

        # Reverse order
        comments = comments[::-1]

        for c in comments:
            comment_body = c['body']
            comment_author = c['author']

            payload = {
                'body': comment_body,
            }

            r = ac.post_activecollab(
                'comments/task/{}'.format(task_id), params=payload)

            comment_id = r['single']['id']

            # updates the date fields
            created = convert_date_to_timestamp(c['created'])
            updated = convert_date_to_timestamp(c['updated'])
            ac.put_activecollab('comments/{}'.format(comment_id),
                                {'created_on': created})
            ac.put_activecollab('comments/{}'.format(comment_id),
                                {'updated_on': updated})

            # needs created_by put here as adding the date
            ac.put_activecollab(
                'comments/{}'.format(comment_id),
                {
                    'updated_on': updated,
                    'created_by_id': get_activecollab_user(comment_author),
                    'updated_by_id': get_activecollab_user(comment_author)
                })


def import_attachments(ac_project_id, task_id, fields, jira_auth):
    if 'attachment' in fields:
        for a in fields['attachment']:
            attach_filename = a['filename']
            attach_content = a['content']

            r = requests.get(attach_content, auth=jira_auth)
            with open('attachments/{}'.format(attach_filename),
                      'wb') as jira_file:
                jira_file.write(r.content)

            jira_file = {
                'attachment_1': [
                    attach_filename,
                    open('attachments/{}'.format(attach_filename), 'rb'),
                    a['mimeType']
                ]
            }

            r = ac.upload_activecollab(jira_file)

            file_code = r[0]['code']
            print('Uploaded file {}, got file code: {}'.format(
                attach_filename, file_code))
            r = ac.put_activecollab('projects/{}'.format(
                ac_project_id),
                {'attach_uploaded_files':  [file_code]})
            r = ac.put_activecollab('projects/{}/tasks/{}'.format(
                ac_project_id, task_id),
                {'attach_uploaded_files':  [file_code]})

            try:
                os.remove(jira_file)
            except:
                pass


ISSUE_TYPES_MAPPING = {
    'Bug': 'TASK: ISSUE',
    'Improvement': 'TASK: IMPROVEMENT',
    'New Feature': 'TASK: NEW FEATURE'
}


def get_label_for_issue_type(issue_type):
    if issue_type in ISSUE_TYPES_MAPPING:
        return ISSUE_TYPES_MAPPING[issue_type]

    return None


ISSUE_PRIORITY_MAPPING = {
    'Blocker': 'PRIORITY: MUST',
    'Critical': 'PRIORITY: MUST',
    'Major': 'PRIORITY: SHOULD',
    'Minor': 'PRIORITY: COULD',
    'Trivial': 'PRIORITY: COULD'
}


def get_label_for_priority(priority):
    if priority in ISSUE_PRIORITY_MAPPING:
        return ISSUE_PRIORITY_MAPPING[priority]

    return None


ISSUE_STATUS_LIST_MAPPING = {
    'Open': 'Inbox',
    'In Progress': 'In Progress',
    'Resolved': 'Done',
    'Reopened': 'To Do',
    'Closed': 'Done',
    'Waiting for Feedback': 'To Do'
}


def get_list_for_status(status):
    if status in ISSUE_STATUS_LIST_MAPPING:
        return ISSUE_STATUS_LIST_MAPPING[status]

    return None


ISSUE_STATUS_LABEL_MAPPING = {
    'Waiting for Feedback': 'STATUS: WAITING FOR FEEDBACK',
}


def get_label_for_status(status):
    if status in ISSUE_STATUS_LABEL_MAPPING:
        return ISSUE_STATUS_LABEL_MAPPING[status]

    return None


ISSUE_RESOLUTION_MAPPING = {
    'Fixed': 'STATUS: FIXED',
    'Won\'t Fix': 'STATUS: WONTFIX',
    'Duplicate': 'STATUS: DUPLICATE',
    'Cannot Reproduce': 'STATUS: CANNOT REPRODUCE'
}


def get_label_for_resolution(resolution):
    if resolution in ISSUE_RESOLUTION_MAPPING:
        return ISSUE_RESOLUTION_MAPPING[resolution]

    return None



def get_activecollab_user(jira_user):
    email = jira_user['emailAddress']

    if not email:
        email = '{}@email.not.available'.format(jira_user['key'])

    if email in ac_users:
        return ac_users[email]

    email = '{}.inactive'.format(email)

    if email in ac_users:
        return ac_users[email]

    return create_activecollab_user(email, jira_user['displayName'])


def create_activecollab_user(email, name):
    r = ac.post_activecollab('/users', {
        'type': 'Client',
        'email': email,
        'display_name': name,
        'password': 'this password needs to be reset!'
    })

    if r and 'single' in r and 'id' in r['single']:
        user_id = r['single']['id']
        ac_users[email] = user_id

        return user_id
    else:
        print('Failed to create user for {}'.format(email))

    return AC_DEFAULT_USER


def is_important(priority):
    if priority in ['Blocker', 'Critical']:
        return True

    return False


def is_completed(status):
    if status in ['Resolved', 'Closed']:
        return True

    return False


def convert_date_to_timestamp(value):
    return int(time.mktime(parse(value).timetuple()))


if __name__ == '__main__':
    main()
