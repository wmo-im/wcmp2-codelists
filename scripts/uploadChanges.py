import argparse
import os
import requests

"""
This script uploads TTL files to the defined register
  ./prodRegister or ./testRegister

This requires an authentication token/password, userID and the name of directory with TTL files.
"""


def authenticate(base_url, user_id, password):
    """Constructs authenticated session (with JSESSIONID cookie)."""
    url = f"{base_url}/system/security/apilogin"
    print(f'Authenticating at "{url}"')
    session = requests.Session()
    auth = session.post(url, data={"userid": user_id, "password": password})
    if not auth.status_code == 200:
        raise ValueError("Authentication failed")
    return session


def post(session, url, payload, dry_run, verbose):
    """Posts new content to the intended parent register."""
    headers = {"Content-type": "text/turtle; charset=UTF-8"}
    response = session.get(url, headers=headers)
    # params = {'status':'experimental'}
    params = {"status": "stable"}
    if not dry_run:
        if verbose:
            print(f'  Posting to: "{url}"')
            # print(f'payload: {payload.encode("utf-8")}')
            print(f"    headers: {headers}")
            print(f"    params: {params}")
        res = session.post(url, headers=headers, data=payload.encode("utf-8"), params=params, stream=False)
        if res.status_code != 201:
            print(f'  POST failed with {res.status_code} {res.reason}:\n {res.content.decode("utf-8")}')
        elif verbose:
            print(f"  POST succeeded with {res.status_code} {res.reason}\n")
    else:
        print(f'  Would post to: "{url}"')
        print(f"    headers: {headers}")
        print(f"    params: {params}")


def put(session, url, payload, dry_run, verbose):
    """Updates definition of a register or entity."""
    headers = {"Content-type": "text/turtle; charset=UTF-8"}
    # params = {'status':'experimental'}
    params = {"status": "stable"}
    # for register update adjust the URL
    if "reg:Register" in payload:
        url += "?non-member-properties"
    if not dry_run:
        if verbose:
            print(f'  Putting to: "{url}"')
            # print(f'payload: {payload.encode("utf-8")}')
            print(f"    headers: {headers}")
            print(f"    params: {params}")
        res = session.put(url, headers=headers, data=payload.encode("utf-8"), params=params)
        if res.status_code != 204:
            print(f'  PUT failed with {res.status_code} {res.reason}:\n {res.content.decode("utf-8")}')
        elif verbose:
            print(f"  PUT succeeded with {res.status_code} {res.reason}\n")
    else:
        print(f'  Would put to "{url}"')
        print(f"    headers: {headers}")
        print(f"    params: {params}")


def upload(session, url, payload, dry_run, verbose):
    """PUTs or POSTs given data depending if it already exists or not."""
    headers = {"Content-type": "text/turtle; charset=UTF-8"}
    if verbose:
        print(f"  Checking {url}:", end=" ")
    response = session.get(url, headers=headers)
    if response.status_code == 200:
        if verbose:
            print("Existing entry, using PUT")
        put(session, url, payload, dry_run, verbose)
    elif response.status_code == 404:
        if verbose:
            print("New entry, using POST")
        url = "/".join(url.split("/")[:-1])
        post(session, url, payload, dry_run, verbose)
    else:
        raise ValueError(
            f'Cannot upload to {url}: {response.status_code} {response.reason}:\n {response.content.decode("utf-8")}'
        )


def upload_file(session, rootURL, file_path, dry_run, verbose):
    """Uploads given TTL file to the registry."""
    with open(file_path, "r", encoding="utf-8") as file:
        ttl_data = file.read()
        relID = file_path.replace(".ttl", "")
        url = f"{rootURL}/{relID}"
        print(f"Uploading {file_path}")
        upload(session, url, ttl_data, dry_run, verbose)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("user_id", help='User ID, in form "https://api.github.com/users/<my_id>"')
    parser.add_argument(
        "pass_code", help='Password or token generated at "https://ci.codes.wmo.int/ui/temporary-password"'
    )
    parser.add_argument("mode", help='Mode: "test" or "prod"')
    parser.add_argument("directory", help="Name of the folder with TTL files to upload.")
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Only print what would be uploaded without actually sending anything.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print more details.")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        raise ValueError(f'Directory "{args.directory}" does not exists.')
    if args.mode not in ["test", "prod"]:
        raise ValueError('Mode must be either "test" or "prod"')
    if args.mode == "prod":
        with open("prodRegister", "r", encoding="utf-8") as fh:
            base_url = fh.read().split("\n")[0]
    elif args.mode == "test":
        with open("testRegister", "r", encoding="utf-8") as fh:
            base_url = fh.read().split("\n")[0]

    print(f"Running upload with respect to {base_url}")

    session = authenticate(base_url, args.user_id, args.pass_code)
    for root, dirs, files in os.walk(args.directory):
        for file_ in files:
            if file_.endswith(".ttl"):
                filename = os.path.join(root, file_)
                upload_file(session, base_url, filename, args.dry_run, args.verbose)
