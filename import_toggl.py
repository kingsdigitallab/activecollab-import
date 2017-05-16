#!/usr/bin/env python

import requests

import activecollab as ac
import simplejson

from time import gmtime, strftime

ac_users = ac.get_activecollabusers()

TOGGL_PROJECTS_URL = 'https://www.toggl.com/api/v8/projects/'

toggl_projects = {}

with open('toggl_projects_to_import.json') as f:
    toggl_projects = simplejson.loads(f.read())


def main():
    with open('toggl_secrets.json.nogit') as f:
        secrets = simplejson.loads(f.read())

    toggl_auth = (secrets['username'], secrets['password'])
    current_date = strftime('%Y-%m-%d', gmtime())

    for toggl_project_id in toggl_projects:
        ac_project_id = toggl_projects[toggl_project_id]

        print(toggl_project_id)

        r = requests.get('{}{}'.format(TOGGL_PROJECTS_URL, toggl_project_id),
                         auth=toggl_auth)

        if r.status_code == 200:
            data = r.json()['data']
            name = data['name']
            print(name)

            params = {
                'value': data['actual_hours'],
                'job_type_id': 1,
                'user_id': 32,
                'record_date': current_date,
                'summary': 'Total time imported from Toggl'
            }

            post = ac.post_activecollab(
                'projects/{}/time-records'.format(ac_project_id),
                params=params)

            if 'single' not in post:
                print('Failed to add time record for {}'.format(name))
        else:
            print('Failed to get data for {}'.format(toggl_project_id))

        print()


if __name__ == '__main__':
    main()
