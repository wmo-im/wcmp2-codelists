import argparse
import json
import os

import requests

"""
This script uploads content to the defined register
  ./prodRegister or ./testRegister

This reqires an authentication token and userID and structured
content.

The structured content is taken from the command line positional argument
uploads
which may either consist of a path to a JSON encoded file or an explicit JSON string
The JSON payload shall be a dictionary with the keys:
  'PUT', 'POST'
and each key shall provide a list of .ttl files to upload to prodRegister
based on the relative path of the .ttl file.

"""

def authenticate(session, base, userid, pss, dry_run):
    # Prefer HTTPS for registry session interactions
    # Essential for authenticate due to 405 response
    if base.startswith('http://'):
        base = base.replace('http://', 'https://')
    url = f'{base}/system/security/apilogin'
    auth = session.post(url, data={'userid':userid, 'password':pss})
    if dry_run:
        print(f'Authenticating at: "{url}"')
        print(f'Result: "{auth}"')

    if not auth.status_code == 200:
        raise ValueError('auth failed')

    return session

def parse_uploads(uploads):
    result = json.loads(uploads)
    if set(result.keys()) != set(('PUT', 'POST')):
        raise ValueError("Uploads inputs should have keys"
                         " set(('PUT', 'POST')) only, not:\n"
                         "{}".format(result.keys()))
    return result

def post(session, url, payload):
    # Prefer HTTPS for registry session interactions
    if url.startswith('http://'):
        url = url.replace('http://', 'https://')
    # POST new content to the intended parent register
    headers={'Content-type':'text/turtle; charset=UTF-8'}
    response = session.get(url, headers=headers)
    params = {'status':'experimental'}
    # params = {'status':'stable'}
    if not dry_run:
        res = session.post(url, headers=headers, data=payload.encode("utf-8"),
                           params=params)
        if res.status_code != 201:
            print('POST failed with {}\n{}'.format(res.status_code, res.reason))
    else:
        print(f'Would post to: "{url}"')
        print(f'payload: {payload.encode("utf-8")}')
        print(f'params: {params}')


def put(session, url, payload, dry_run):
    # Prefer HTTPS for registry session interactions
    if url.startswith('http://'):
        url = url.replace('http://', 'https://')
    # PUT updated content to the entity already registered
    headers={'Content-type':'text/turtle; charset=UTF-8'}
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError('Cannot PUT to {}, it does not exist.'.format(url))
    params = {'status':'experimental'}
    if not dry_run:
        res = session.put(url, headers=headers, data=payload.encode("utf-8"),
                          params=params)
    else:
        print(f'Would put to "{url}"')
        print(f'payload: {payload.encode("utf-8")}')
        print(f'params: {params}')

def post_uploads(session, rootURL, uploads, dry_run):
    for postfile in uploads:
        with open('.{}'.format(postfile), 'r', encoding="utf-8") as pf:
            pdata = pf.read()
        # post, so remove last part of identity, this is in the payload
        relID = postfile.replace('.ttl', '')
        relID = '/'.join(postfile.split('/')[:-1])
        url = '{}{}'.format(rootURL, relID)
        print(url)
        post(session, url, pdata, dry_run)

def put_uploads(session, rootURL, uploads, dry_run):
    for putfile in uploads:
        with open('.{}'.format(putfile), 'r', encoding="utf-8") as pf:
            pdata = pf.read()
        relID = putfile.replace('.ttl', '')
        url = '{}{}'.format(rootURL, relID)
        print(url)
        put(session, url, pdata, dry_run)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('user_id')
    parser.add_argument("passcode")
    parser.add_argument("tmode")
    parser.add_argument('uploads')
    parser.add_argument('-n', '--dry-run', action="store_true",
                        help='Only print what would be uploaded without actually sending anything.')
    args = parser.parse_args()

    if os.path.exists(args.uploads):
        with open(args.uploads, 'r') as ups:
            uploads = ups.read()
    else:
        uploads = args.uploads
    uploads = parse_uploads(uploads)
    if args.tmode not in ['test', 'prod']:
        raise ValueError('test mode must be either "test" or "prod"')
    if args.tmode == 'prod':
        with open('prodRegister', 'r', encoding='utf-8') as fh:
            rooturl = fh.read().split('\n')[0]
            print('Running upload with respect to {}'.format(rooturl))
    elif args.tmode == 'test':
        with open('testRegister', 'r', encoding='utf-8') as fh:
            rooturl = fh.read().split('\n')[0]
            print('Running upload with respect to {}'.format(rooturl))

    session = requests.Session()
    session = authenticate(session, rooturl, args.user_id, args.passcode, args.dry_run)
    print(uploads)
    post_uploads(session, rooturl, uploads['POST'], args.dry_run)
    put_uploads(session, rooturl, uploads['PUT'], args.dry_run)

