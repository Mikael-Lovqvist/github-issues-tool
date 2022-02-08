# github-issues-tool
Tool for managing github issues in python files that utilizes the `tokenize` module in python

**IMPORTANT**: without `--read-only` files will be modified and there might be bugs in here because this is very young and untested so be careful!

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
