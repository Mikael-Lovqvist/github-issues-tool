# github-issues-tool
Tool for managing github issues in python files that utilizes the `tokenize` module in python

**IMPORTANT**: without `--read-only` files will be modified and there might be bugs in here because this is very young and untested so be careful!

# Operation

This tool will go through `.py` files and look for a few special comments  
Note that `[]` denotes optional match and `{}` denotes a place holder for a named entry and `{...}` denotes optional repeat of previous item.

## Create new issue

```python
#ISSUE[:] {title}
#	{body}
#	{...}
#	labels: {label}, {...}
```
This will create a new issue with the title `title` and the optional body `body`.  
On a single line you can also specify one or more `label` as a comma separated list.  
Currently this new issue doesn't reference the file or any other automatic function but this might be changed in the future.  

After this issue is registered it will be updated to `#ISSUE-{number}` unless `--read-only` is specified.  
Note that if you specify `--dry-run` you will get a number here that is just a mock number since it will not communicate with `github.com`.

## Update issue

When an already registered issue is encountered it will check if its `state` is `closed`.
If this is the case the entire comment will be removed from the source file.

## Close an issue

```python
#CLOSE ISSUE-{number}[:] [{message}]
```
This will close the issue. If `message` is specified a comment will be made with its message prior to closing the issue.



# Usage

```
usage: gh-issues-tool.py [-h] [-R] [-D] [-r] [--token-file TOKEN_FILE] [--user USER] [--repo REPO] search_path

positional arguments:
  search_path

options:
  -h, --help            show this help message and exit
  -R, --recursive
  -D, --dry-run
  -r, --read-only
  --token-file TOKEN_FILE
  --user USER
  --repo REPO
```

Current usage specifies a path `search_path` that will be searched for python files.  
If `--recursive` is specified it will descent into sub directories from `search_path`.  
When `--dry-run` is specified, no communication with `github.com` will take place.  
In order to use this with `github.com` you need to specify the following:  
  `--token-file`: Path to a file that contains the github token used for authentication.  
  `--user`: Your github username  
  `--repo`: The repository to access  
