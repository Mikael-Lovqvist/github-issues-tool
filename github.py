import requests
from pathlib import Path

def enable_verbose_logging():
	import logging
	import http.client as http_client
	http_client.HTTPConnection.debuglevel = logging.DEBUG
	logging.basicConfig()
	logging.getLogger().setLevel(logging.DEBUG)
	log = logging.getLogger("requests.packages.urllib3")
	log.setLevel(logging.DEBUG)
	log.propagate = True

def list_dict_proxy(item):
	if isinstance(item, list):
		return list_proxy(item)
	elif isinstance(item, dict):
		return dict_proxy(item)
	else:
		return item

class generic_proxy:
	def __init__(self, data):
		self._data = data

	def __repr__(self):
		return f'{self.__class__.__name__}{self._data}'

class dict_proxy(generic_proxy):
	def __getattr__(self, key):
		return list_dict_proxy(self._data[key])

	def __iter__(self):
		for key, item in self._data.items():
			yield key, list_dict_proxy(item)

class list_proxy(generic_proxy):

	def __getitem__(self, index):
		return list_dict_proxy(self._data[index])

	def __iter__(self):
		for item in self._data:
			yield list_dict_proxy(item)

#TODO - check that results are OK
class github_api:
	def __init__(self, token_from_file=None, token=None, **settings):
		self.token = token
		for key, value in settings.items():
			setattr(self, key, value)

		if token_from_file:
			self.token = Path(token_from_file).read_text().strip()

	def fetch_values(self, data, *settings):
		for name in settings:
			value = data.get(name)
			if value is not None:
				yield value
			else:
				yield getattr(self, name)

	def list_issues(self, user=None, repo=None, **query):
		user, repo = self.fetch_values(locals(), 'user', 'repo')
		return list_dict_proxy(requests.get(f'https://api.github.com/repos/{user}/{repo}/issues', headers=dict(
			accept = 'application/vnd.github.v3+json',
			Authorization = f'token {self.token}',
		), params=query).json())

	def get_issue(self, number, user=None, repo=None):
		user, repo = self.fetch_values(locals(), 'user', 'repo')
		return list_dict_proxy(requests.get(f'https://api.github.com/repos/{user}/{repo}/issues/{number}', headers=dict(
			accept = 'application/vnd.github.v3+json',
			Authorization = f'token {self.token}',
		)).json())

	def create_issue_comment(self, number, body, user=None, repo=None, **query):
		user, repo = self.fetch_values(locals(), 'user', 'repo')
		return list_dict_proxy(requests.post(f'https://api.github.com/repos/{user}/{repo}/issues/{number}/comments', headers=dict(
			accept = 'application/vnd.github.v3+json',
			Authorization = f'token {self.token}',
		), json=dict(
			body=body,
			**query,
		)).json())

	def close_issue(self, number, comment=None, user=None, repo=None, **query):
		user, repo = self.fetch_values(locals(), 'user', 'repo')

		if comment:
			self.create_issue_comment(number, comment, user, repo)

		return list_dict_proxy(requests.patch(f'https://api.github.com/repos/{user}/{repo}/issues/{number}', headers=dict(
			accept = 'application/vnd.github.v3+json',
			Authorization = f'token {self.token}',
		), json=dict(
			state='closed',
			**query,
		)).json())


	def create_issue(self, title, body, user=None, repo=None, **query):
		#query: labels = ['label1', 'label2']
		user, repo = self.fetch_values(locals(), 'user', 'repo')

		return list_dict_proxy(requests.post(f'https://api.github.com/repos/{user}/{repo}/issues', headers=dict(
			accept = 'application/vnd.github.v3+json',
			Authorization = f'token {self.token}',
		), json=dict(
			title=title,
			body=body,
			**query,
		)).json())


class dummy_api:
	def __init__(self):
		self.number = 0

	def create_issue(self, title, body, user=None, repo=None, **query):
		self.number += 1
		print(f'create_issue({locals()})')
		return dict_proxy(dict(
			number = self.number,
			url = 'https://example.org/',
		))

	def get_issue(self, number, user=None, repo=None):
		print(f'get_issue({locals()})')
		return dict_proxy(dict(
			state = 'closed',
			url = 'https://example.org/',
		))

	def close_issue(self, number, comment=None, user=None, repo=None, **query):
		print(f'close_issue({locals()})')
		return dict_proxy(dict(
			url = 'https://example.org/',
		))

