import base64
import json
import re

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
    total = 0
    goal = 50000

    root = api('/repos/{0}/{1}/git/trees/master'.format(user, repo))
    for t in root['tree']:
        if t['path'] == 'ch':
            next_url = t['url']

    subfolder = api(next_url)
    for t in subfolder['tree']:
        if t['path'].endswith('.mkd'):
            f = api(t['url'])
            assert f['encoding'] == 'base64'
            content = base64.decodestring(f['content'].encode())
            total += count_words(content.decode())

    return total, goal


def count_words(story):
    return len(list(filter(None, re.split(r"[^\w']", story))))


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
