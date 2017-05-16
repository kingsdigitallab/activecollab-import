import requests
import simplejson

ac_secrets = {}

with open('ac_secrets.json.nogit') as f:
    ac_secrets = simplejson.loads(f.read())


AC_BASE_URL = 'https://app.activecollab.com/148987/api/v1/'
AC_TOKEN = ac_secrets['ac_token']
AC_HEADERS = {
    'X-Angie-AuthApiToken': AC_TOKEN,
    'Content-Type': 'application/json; charset=utf-8'
}

AC_HEADERS_UPLOAD = {
    'X-Angie-AuthApiToken': AC_TOKEN
}


def get_activecollabusers():
    ac_users = {}
    users = get_activecollab('users')

    for user in users:
        ac_users[user['email']] = user['id']

    return ac_users


def get_activecollab(api_path, params=None):
    r = requests.get('{}{}'.format(
        AC_BASE_URL, api_path), params=simplejson.dumps(params),
        headers=AC_HEADERS)

    return r.json()


def get_activecollab_tasklists(project):
    ac_tasklists = {}
    tasklists = get_activecollab('projects/{}/task-lists'.format(project))

    for tl in tasklists:
        ac_tasklists[tl['name']] = tl['id']

    return ac_tasklists


def post_activecollab(api_path, params=None):
    r = requests.post('{}{}'.format(
        AC_BASE_URL, api_path), data=simplejson.dumps(params),
        headers=AC_HEADERS)

    return r.json()


def put_activecollab(api_path, params=None):
    r = requests.put('{}{}'.format(AC_BASE_URL, api_path),
                     data=simplejson.dumps(params), headers=AC_HEADERS)
    return r.json()


def upload_activecollab(files):
    r = requests.post('{}upload-files'.format(
        AC_BASE_URL), files=files, headers=AC_HEADERS_UPLOAD)
    return r.json()
