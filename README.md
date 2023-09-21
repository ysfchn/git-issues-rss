# git-issues-rss

A very-basic Atom feed (RSS-like web feed format) generator/API for tracking new issues and comments in a given hosted Git repository, which can be pretty useful for seeing what's happening recently in your favorite project. Coded in Python and hosted on Vercel.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fysfchn%2Fgit-issues-rss)

## Usage

```
https://<DEPLOY-URL>/api/feed
```

Query parameters:

* `repo` (**Required**)
    * Repository name in `account/repo` format which the slash (`/`) is encoded as `%2F`, such as `?repo=microsoft%2Fvscode`.
* `host_type` (**Required**)
    * One of these constants: `github`, `forgejo` or `gitea` to specify where the repository is hosted. This value determines the defaults of `git_host`, `api_host`, `api_comments` and `api_issues` parameters.
* `since`
    * Timestamp in ISO format (like `2023-09-20T07:11:00+00:00`) to filter created issues and comments after given date. If not given, issues and comments will be listed 2 days ago from the time of the feed has requested. To refer the plus sign (`+`) use it in the encoded form `%2B`, as plus signs are normally used for space (` `) characters in URLs. 

Advanced:

* `pretty`
    Set it to any value to display a pretty (newlines, indentations) XML output. Not including this parameter will display a minified XML (the default), which results in a smaller feed file.
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