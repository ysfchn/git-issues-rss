# git-issues-rss

An [Atom XML feed](https://wikipedia.org/wiki/Atom_(web_standard)) API for tracking new issues and comments in a given hosted git repository, which can be pretty useful for seeing what's happening recently in your favorite project.

The generated feed aims to be compatible with [RFC 4287](https://datatracker.ietf.org/doc/html/rfc4287) and with [RFC 5005](https://datatracker.ietf.org/doc/html/rfc5005) for pagination of the feed. It is generated on-the-fly without use of databases and it queries issues and comments in bulk. Feed entries represent an issue or a comment, comments will have the same title with issues that the comment posted in, but only if issue itself is seen in the feed, which means the generator will avoid sending a HTTP request just for reading a single issue.

It supports public GitHub repositories and public repositories in Gitea/Forgejo instances. See below for usage.

Note that the feed doesn't limit the queried issues and comments (it just lists what the API returns, but it might be changed in the future), so this might cause unwanted behavior in more active repositories, and the feed doesn't support pagination at the moment.

Written in Python and can be hosted easily on Vercel with the button down below.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fysfchn%2Fgit-issues-rss)

## Usage

```
https://<DEPLOY-URL>/api/feed
```

> Make sure to encode characters query parameters properly before making an request.

Query parameters:

* `repo` (**Required**)
    * Repository name in `account/repo` format which the slash (`/`) is encoded as `%2F`, such as `?repo=microsoft%2Fvscode`.
* `host_type` (**Required**)
    * One of these constants: `github`, `forgejo` or `gitea` to specify where the repository is hosted. This value determines the defaults of `git_host`, `api_host`, `api_comments` and `api_issues` parameters.
* `since`
    * Timestamp in ISO format (like `2023-09-20T07:11:00+00:00`) to filter created issues and comments after given date. If not given, feed will be limited to 2 days ago from the time of the feed has requested. To refer the plus sign (`+`) use it in the encoded form `%2B`, as plus signs are normally used for space (` `) characters in URLs.

Advanced:

* `pretty`
    * Set it to any value to display a XML output with newlines and indentations. Not including this parameter will display a minified XML (the default), which results in a smaller feed file and thus less bandwidth usage.
* `limit`
    Maximum entries that is shown on the feed per page. Default is 50.
* `page`
    Number of the page to fetch issues and comments. First page contains the latest updates. Default is 1.
* `git_host`
    * Hostname of the related git hosting service. The value is determined by `host_type`, but can be overriden by setting this parameter. If not specified, the default values are:
        * If `host_type` is `github`, the default will be set to: `github.com`.
        * If `host_type` is `forgejo`, the default will be set to: `codeberg.org`.
        * If `host_type` is `gitea`, the default will be set to: `gitea.com`.
* `api_host`
    * Hostname of the related git hosting's API service. The value is determined by `host_type`, but can be overriden by setting this parameter. If not specified, the default values are:
        * If `host_type` is `github`, the default will be set to: `api.github.com`.
        * If `host_type` is `forgejo`, the default will be set to: `codeberg.org`.
        * If `host_type` is `gitea`, the default will be set to: `gitea.com`.
* `api_issues`
    * Endpoint of querying the issues in the related git hosting service. The value is determined by `host_type`, but can be overriden by setting this parameter. If not specified, the default values are:
        * If `host_type` is `github`, the default will be set to: `/repos/{0}/issues`.
        * If `host_type` is `forgejo`, the default will be set to: `/api/v1/repos/{0}/issues`.
        * If `host_type` is `gitea`, the default will be set to: `/api/v1/repos/{0}/issues`.
* `api_comments`
    * Endpoint of querying the comments in the related git hosting service. The value is determined by `host_type`, but can be overriden by setting this parameter. If not specified, the default values are:
        * If `host_type` is `github`, the default will be set to: `/repos/{0}/issues/comments`.
        * If `host_type` is `forgejo`, the default will be set to: `/api/v1/repos/{0}/issues/comments`.
        * If `host_type` is `gitea`, the default will be set to: `/api/v1/repos/{0}/issues/comments`.

## Examples

```
https://<DEPLOY-URL>/api/feed?repo=Freeyourgadget%2FGadgetbridge&host_type=forgejo
```

```
https://<DEPLOY-URL>/api/feed?repo=microsoft%2Fvscode&host_type=github&since=2023-09-21T00:00:00%2b03:00
```

The feed will look like:

```xml
<?xml version="1.0" ?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>microsoft/vscode issue updates</title>
    <link rel="alternate" href="https://github.com/microsoft/vscode/issues"/>
    <icon>https://github.com/favicon.ico</icon>
    <updated>2023-09-21T22:06:14+00:00</updated>
    <id>urn:uuid:00000000-0000-4000-8000-0000d4cc983a</id>
    ...
    <entry>
        <title type="text">Add way to set ID for a localization string?</title>
        <link rel="alternate" href="https://github.com/microsoft/vscode/issues/193738"/>
        <author>
            <name>jruales</name>
        </author>
        <id>urn:uuid:00000000-0000-4000-8000-00000002f4ca</id>
        <category term="comment"/>
        <published>2023-09-21T20:34:00+00:00</published>
        <updated>2023-09-21T22:03:52+00:00</updated>
        <content type="text/markdown">
            Currently, each string is assigned an ID based on a hash of the English string and the comment. The problem with this is that any small change to a string or its comment will change the ID, requiring a new translation from scratch. It might be good to allow the user to specify an ID to use for a given English string. That way, if the user makes a small change to the English string, the ID will remain the same, and the translator will be able to use the old translation as a basis for the new translation, only changing the small part that was modified in the English string.
        </content>
    </entry>
    ...
</feed>
```

## Development

To avoid messing with your system-wide Python dependencies, use [Rye](https://rye-up.com/) to set up an virtual environment in the easiest way.

```
rye sync
```

Then, run the file to locally test the endpoint:

```
python api/feed.py
```

If you don't want to use a virtual environment at all, you can also install the dependencies to your current Python installation:

```
pip install -r requirements.txt
```

## License

This project is licensed with GPLv3.