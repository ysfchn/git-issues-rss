import httpx
from datetime import datetime, timezone, timedelta
from typing import NamedTuple, List, Dict, Generator, Union, Any, Optional, Tuple
from http.server import BaseHTTPRequestHandler, HTTPServer
from itertools import chain
from urllib.parse import parse_qs, urlencode
from xml.dom import minidom
from functools import partial
from zlib import crc32
import orjson
from uuid import UUID

class CommentData(NamedTuple):
    uuid : str
    link : str
    title : str
    content : str
    author : str
    published : datetime
    updated : datetime

class IssueData(NamedTuple):
    uuid : str
    link : str
    title : str
    content : str
    author : str
    published : datetime
    updated : datetime

HOSTS = {
    "github": {
        "api_host": "api.github.com",
        "git_host": "github.com",
        "issues": "/repos/{0}/issues",
        "comments": "/repos/{0}/issues/comments"
    },
    "gitea": {
        "api_host": "gitea.com",
        "git_host": "gitea.com",
        "issues": "/api/v1/repos/{0}/issues",
        "comments": "/api/v1/repos/{0}/issues/comments"
    },
    "forgejo": {
        "api_host": "codeberg.org",
        "git_host": "codeberg.org",
        "issues": "/api/v1/repos/{0}/issues",
        "comments": "/api/v1/repos/{0}/issues/comments"
    }
}

def get_datetime_now():
    return datetime.now(timezone.utc).astimezone()

def datetime_to_iso(date : datetime):
    return date.isoformat(timespec = "seconds")

def iso_to_datetime(iso : str):
    if iso.endswith("Z"):
        return iso_to_datetime(iso[:-1])
    return datetime.fromisoformat(iso).astimezone(timezone.utc)

def yield_issue_updates(
    repo : str,
    since : datetime,
    api_host : str,
    api_issues : str,
    api_comments : str,
    page : int = 1,
    limit : int = 50
) -> Generator[Union[CommentData, IssueData], None, Optional[Tuple[int, str]]]:
    """
    Requests issues and comments from "since" datetime 
    objects and yields both issues and comments.
    """
    client = httpx.Client(
        base_url = "https://{0}".format(api_host), 
        trust_env = False
    )
    issues = client.get(
        api_issues.format(repo), 
        params = {
            "since": datetime_to_iso(since),
            "page": page,
            ("per_page" if api_host == "api.github.com" else "limit"): limit
        }
    )
    comments = client.get(
        api_comments.format(repo), 
        params = {
            "since": datetime_to_iso(since),
            "page": page,
            ("per_page" if api_host == "api.github.com" else "limit"): limit
        }
    )
    issues_list : List[Dict[str, Union[str, Any]]] = orjson.loads(issues.content)
    comments_list : List[Dict[str, Union[str, Any]]] = orjson.loads(comments.content)
    client.close()
    if issues.status_code != 200:
        return (issues.status_code, "From server: " + issues_list["message"],)
    elif comments.status_code != 200:
        return (comments.status_code, "From server: " + comments_list["message"],)
    comments_on_issues : Dict[str, List[CommentData]] = {}
    for c in comments_list:
        issue_number : str = c["issue_url"].split("/")[-1]
        # Ignore pull requests.
        if (not issue_number):
            continue
        if ("/pulls/" in c["issue_url"]) or ("/pull/" in c["html_url"]):
            continue
        if issue_number not in comments_on_issues:
            comments_on_issues[issue_number] = []
        uuid_obj = UUID(int = int(c["id"]), version = 4)
        comments_on_issues[issue_number].append(CommentData(
            uuid = str(uuid_obj),
            link = c["html_url"],
            title = f"Comment on issue #{issue_number}",
            content = c["body"] or "",
            author = c["user"]["login"],
            published = iso_to_datetime(c["created_at"]),
            updated = iso_to_datetime(c["updated_at"])
        ))
    for i in issues_list:
        issue_number = str(i["number"])
        published = iso_to_datetime(i["created_at"])
        # Ignore pull requests.
        if ("/pulls/" in c["html_url"]) or ("/pull/" in c["html_url"]):
            continue
        # When an issue gets a new comment, the issue becomes
        # "updated". So, this will cause displaying the issue
        # even if it is old. To prevent that, we explicitly check
        # if issue is newly created.
        if since > published:
            continue
        uuid_obj = UUID(int = int(issue_number), version = 4)
        yield IssueData(
            uuid = str(uuid_obj),
            link = i["html_url"],
            title = i["title"],
            content = i["body"] or "",
            author = i["user"]["login"],
            published = published,
            updated = iso_to_datetime(i["updated_at"])
        )
        for c in comments_on_issues.get(issue_number, [])[:]:
            yield c._replace(title = "Comment on: " + i["title"])
            comments_on_issues[issue_number].remove(c)
    for v in comments_on_issues.values():
        for c in v:
            yield c


def add_element(
    _root : minidom.Document,
    _parent : Optional[minidom.Element] = None,
    _tag : str = "link",
    _content : Optional[str] = None,
    /,
    **kwargs
):
    el = _root.createElement(_tag)
    if _content:
        el.appendChild(_root.createTextNode(_content))
    for k, v in kwargs.items():
        el.setAttribute(k, v)
    if _parent:
        _parent.appendChild(el)
    return el


def get_updates_atom(
    host_url : str,
    repo : str,
    since : datetime,
    api_host : str,
    git_host : str,
    api_issues : str,
    api_comments : str,
    host_type : str,
    title : Optional[str] = None,
    pretty : bool = False,
    page : int = 1,
    limit : int = 50
) -> str:
    """
    Create an atom feed with updates.
    """
    root = minidom.Document()
    updates_url = "https://{0}/{1}/issues".format(git_host, repo)
    element = partial(add_element, root)
    # Create elements
    feed = element(root, "feed", xmlns = "http://www.w3.org/2005/Atom")
    element(feed, "title", title or (repo + " issue updates"))
    element(
        feed, "subtitle", 
        "Feed of latest issues and comments for Git repositories."
    )
    element(feed, "id", "urn:uuid:" + str(
        UUID(int = crc32(repo.encode()), version = 4)
    ))
    element(feed, "icon", "https://" + git_host + "/favicon.ico")
    element(feed, "link", rel = "alternate", href = updates_url)
    element(feed, "generator", "git-issues-rss", uri = "https://github.com/ysfchn/git-issues-rss")
    constructed = {
        "repo": repo,
        "since": datetime_to_iso(since),
        "host_type": host_type,
        "api_host": api_host,
        "git_host": git_host,
        "api_issues": api_issues,
        "api_comments": api_comments,
        "pretty": 1 if pretty else 0,
        "title": title or (repo + " issue updates"),
        "page": page,
        "limit": limit
    }
    if page > 1:
        element(feed, "link", rel = "previous", href = host_url + "?" + urlencode({
            **constructed, "page": constructed["page"] - 1
        }))
    element(feed, "link", rel = "next", href = host_url + "?" + urlencode({
        **constructed, "page": constructed["page"] + 1
    }))
    feed_updated = element(feed, "updated")
    last_update = datetime.fromtimestamp(0, timezone.utc)
    post_generator = yield_issue_updates(
        repo = repo, 
        since = since,
        api_host = api_host,
        api_issues = api_issues,
        api_comments = api_comments,
        page = page,
        limit = limit
    )
    first_post = None
    try:
        first_post = next(post_generator)
    except StopIteration as exc:
        if exc.value:
            raise exc
        first_post = []
    else:
        first_post = [first_post]
    for post in chain(first_post, post_generator):
        post_type = "issue" if isinstance(post, IssueData) else "comment"
        entry = element(feed, "entry")
        element(entry, "title", post.title, type = "text")
        element(entry, "link", rel = "alternate", href = post.link)
        entry_author = element(entry, "author")
        element(entry_author, "name", post.author)
        element(entry, "id", "urn:uuid:" + post.uuid)
        element(entry, "category", term = post_type)
        element(entry, "published", post.published.isoformat(timespec = "seconds"))
        element(entry, "updated", post.updated.isoformat(timespec = "seconds"))
        element(entry, "content", post.content, type = "text/markdown")
        if post.updated > last_update:
            last_update = post.updated
    feed_updated.appendChild(root.createTextNode(
        last_update.isoformat(timespec = "seconds")
    ))
    if pretty:
        return root.toprettyxml(indent = " " * 4)
    else:
        return root.toxml()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(self.path.split("?", 1)[-1])
        if ("repo" not in params) or ("host_type" not in params):
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(orjson.dumps({
                "code": 400,
                "message": "'repo' or 'host_type' query parameter is missing."
            }))
            return
        since_time = None
        host_type = HOSTS.get(params["host_type"][0], HOSTS["github"])
        if "git_host" in params:
            host_type["git_host"] = params["git_host"][0]
        if "api_host" in params:
            host_type["api_host"] = params["api_host"][0]
        if "api_comments" in params:
            host_type["api_comments"] = params["api_comments"][0]
        if "api_issues" in params:
            host_type["api_issues"] = params["api_issues"][0]
        if "since" in params:
            since_time = iso_to_datetime(params["since"][0])
        try:
            atom = get_updates_atom(
                host_url = (
                    ("http://" if ":" in self.headers["Host"] else "https://") +
                    self.headers["Host"] + self.path.split("?")[0]
                ),
                repo = params["repo"][0],
                since = since_time or (get_datetime_now() - timedelta(days = 2)),
                title = params.get("title", [None])[0],
                host_type = params["host_type"][0],
                api_host = host_type["api_host"],
                git_host = host_type["git_host"],
                api_comments = host_type["comments"],
                api_issues = host_type["issues"],
                pretty = "pretty" in params,
                page = int(params.get("page", [1])[0]),
                limit = int(params.get("limit", [50])[0])
            )
            self.send_response(200)
            self.send_header("Content-type", "application/atom+xml")
            self.end_headers()
            self.wfile.write(atom.encode())
        except StopIteration as si:
            self.send_response(si.value[0])
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(orjson.dumps({
                "code": si.value[0],
                "message": si.value[1]
            }))
        except orjson.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(orjson.dumps({
                "code": 400,
                "message": "Can't decode JSON."
            }))


if __name__ == "__main__":
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, handler)
    print("Serving on http://{0}:{1}".format(httpd.server_name, httpd.server_port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass