import base64
import json
import re
from fnmatch import fnmatch

import configargparse
import requests
from flask import Flask, render_template, Response

from wordcounter.cache import Cache


p = configargparse.ArgParser(default_config_files=['wordcounter.conf'])
p.add('--gh-token', required=True, env_var='GH_TOKEN', help='GitHub API Token.')
p.add('--gh-api-url', default='https://api.github.com', env_var='GH_API_URL', help='GitHub API URL')
p.add('--port', default=5000, type=int, env_var='PORT', help='Port to bind to.')
p.add('--host', default='0.0.0.0', env_var='HOST', help='Host to bind to.')
p.add('--debug', default=False, action='store_true', env_var='DEBUG', help='Enable debug mode.')
options = None


app = Flask(__name__)
cache = Cache(timeout=600)


@app.route('/<user>/<repo>.svg')
def badge(user, repo):
    words, goal = get_word_count(user, repo)
    badge_svg = render_template('progress.svg', progress=words / goal, words=words)
    return Response(badge_svg, mimetype='image/svg+xml')


@cache(key='{0}/{1}::wordcount', timeout=600)
def get_word_count(user, repo):
    endpoint = '/repos/{0}/{1}/git/trees/master'.format(user, repo)
    config = get_repo_config(endpoint)
    chapter_blob = config.get('chapterBlob', '*.txt')
    total = sum(count_words(get_blob_contents(blob_url))
                for blob_url
                in get_blob_urls_from_glob(endpoint, chapter_blob))
    goal = config.get('goal', 50000)
    return total, goal


def get_repo_config(tree_url):
    data = api(tree_url)
    content = None
    for o in data['tree']:
        if o['type'] == 'blob' and o['path'] == '.nanowrimo':
            content = get_blob_contents(o['url'])
            break
    if content is None:
        return {}
    else:
        return json.loads(content)


def get_blob_urls_from_glob(tree_url, glob):
    if '/' in glob:
        glob_head, glob_tail = glob.split('/', 1)
    else:
        glob_head, glob_tail = glob, None

    data = api(tree_url)
    for o in data['tree']:
        if fnmatch(o['path'], glob_head):
            if glob_tail is None and o['type'] == 'blob':
                yield o['url']
            elif glob_tail is not None and o['type'] == 'tree':
                yield from get_blob_urls_from_glob(o['url'], glob_tail)


def get_blob_contents(blob_url):
    blob = api(blob_url)
    assert blob['encoding'] == 'base64'
    content = base64.decodestring(blob['content'].encode())
    return content.decode()


def count_words(story):
    return len(list(filter(None, re.split(r"[^\w']", story))))


@cache(key='GET {0}', timeout=30)
def api(url):
    if not re.match(r'^https?://', url):
        url = options.gh_api_url + url
    r = requests.get(url, headers={
        'Authorization': 'Token ' + options.gh_token,
    })
    print(url)
    return r.json()


if __name__ == '__main__':
    options = p.parse_args()
    app.run(host=options.host, port=options.port, debug=options.debug)
