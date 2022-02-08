#!/usr/bin/env python3
from pathlib import Path
import tokenize, operator, re, argparse
import token as TOKEN
from utils import simple_pattern, simple_structure, enumerate_pending, iter_span
import github


class pattern:
	existing_issue = 		simple_pattern(r'#ISSUE-([0-9]+):?(.*)$')
	new_issue = 			simple_pattern(r'#(ISSUE):?(.*)$')
	close_issue = 			simple_pattern(r'#CLOSE\s+ISSUE-([0-9]+):?(.*)$')

	labels =				simple_pattern(r'^labels:?(.*)$', re.I)

class structure:
	#token matching
	matching_comment = 		simple_structure('index pattern match')

	#issues
	new_issue = 			simple_structure('tag_span full_span body')
	existing_issue = 		simple_structure('id full_span body')
	issue_to_be_closed = 	simple_structure('id full_span body')

	#text manipulation
	pending_replacement =	simple_structure('span value')
	pending_erasure =		simple_structure('span')

def priority_match(container, string, *named_patterns):
	for name in named_patterns:
		pattern = getattr(container, name)
		if match := pattern.match(string):
			return name, match

def get_all_matching_comments(token_stream):
	result = list()
	for index, token in enumerate(token_stream):
		if token.type == TOKEN.COMMENT:
			if match := priority_match(pattern, token.string, 'close_issue', 'existing_issue', 'new_issue'):
				result.append(structure.matching_comment(index, *match))
	return result

def extract_issues_from_token_stream(token_stream, line_col_to_pos):
	def extract_body(issue_body):
		first_index = match.index
		for body_index in iter_span(match, pending, len(token_stream), operator.attrgetter('index'), start_offset=1):
			token = token_stream[body_index]

			if token.type == TOKEN.COMMENT:
				issue_body.append(token.string.lstrip('#').strip())
			elif token.type == TOKEN.NL:
				pass
			else:
				break

			last_index = body_index

		while token_stream[last_index].type == TOKEN.NL:
			last_index -= 1

		return first_index, last_index, issue_body


	#Get all matching comments
	matching_comments = get_all_matching_comments(token_stream)

	#Go through matching comments and the tokens between them
	for match, pending in enumerate_pending(matching_comments):
		if match.pattern == 'existing_issue':
			first_index, last_index, body = extract_body([match.match.group(2).strip()])
			full_span = line_col_to_pos(*token_stream[first_index].start), line_col_to_pos(*token_stream[last_index].end)
			yield structure.existing_issue(int(match.match.group(1)), full_span, body)

		elif match.pattern == 'new_issue':
			first_index, last_index, body = extract_body([match.match.group(2).strip()])

			full_span = line_col_to_pos(*token_stream[first_index].start), line_col_to_pos(*token_stream[last_index].end)

			line_tag_span = match.match.span(1)
			row, col = token_stream[first_index].start
			tag_span = line_col_to_pos(row, col + line_tag_span[0]), line_col_to_pos(row, col + line_tag_span[1])

			yield structure.new_issue(tag_span, full_span, body)

		elif match.pattern == 'close_issue':

			first_index, last_index, body = extract_body([match.match.group(2).strip()])
			full_span = line_col_to_pos(*token_stream[first_index].start), line_col_to_pos(*token_stream[last_index].end)

			yield structure.issue_to_be_closed(int(match.match.group(1)), full_span, body)

		else:
			raise Exception()


def perform_text_operations(text, pending_operations, offset=0):
	for operation in pending_operations:
		if isinstance(operation, structure.pending_replacement):
			start, stop = operation.span
			text = text[:start+offset] + operation.value + text[stop+offset:]
			offset += len(operation.value) - stop + start

		elif isinstance(operation, structure.pending_erasure):
			start, stop = operation.span
			text = text[:start+offset] + text[stop+offset:]
			offset += start - stop

	return text, offset

def extract_labels_from_body(body):
	new_body = list()
	labels = set()
	for line in body:
		if m := pattern.labels.match(line):
			labels |= set(map(str.strip, m.group(1).split(',')))
		else:
			new_body.append(line)

	return new_body, list(labels)






def process_file(filename, github_api=github.dummy_api(), read_only=False):

	line_pos_aggregate = dict()
	aggregate = 0
	with open(filename, 'r') as infile:
		file_text = infile.read()

	file_lines = [f'{line}\n' for line in file_text.split('\n')]

	for row, line in enumerate(file_lines, 1):
		line_pos_aggregate[row] = aggregate
		aggregate += len(line)

	def line_col_to_pos(row, col):
		return line_pos_aggregate[row] + col

	token_stream = list(tokenize.generate_tokens(iter(file_lines).__next__))

	pending_operations = list()

	#Use tuple so that we have exhausted the iterator - we don't want to have a problem half way through!
	for issue in tuple(extract_issues_from_token_stream(token_stream, line_col_to_pos)):

		if isinstance(issue, structure.new_issue):
			#Register issue and write back new ID
			title = issue.body[0]
			body, labels = extract_labels_from_body(issue.body[1:])
			registered_issue = github_api.create_issue(title, '\n'.join(body), labels=labels)
			pending_operations.append(structure.pending_replacement(issue.tag_span, f'ISSUE-{registered_issue.number}'))
			print(f'Created issue: {registered_issue.url}')

		elif isinstance(issue, structure.existing_issue):
			#Check if issue is resolved, if so, erase it
			registered_issue = github_api.get_issue(issue.id)
			if registered_issue.state == 'closed':
				print(f'Issue has been closed: {registered_issue.url}')
				pending_operations.append(structure.pending_erasure(issue.full_span))

		elif isinstance(issue, structure.issue_to_be_closed):
			registered_issue = github_api.close_issue(issue.id, '\n'.join(issue.body))
			pending_operations.append(structure.pending_erasure(issue.full_span))
			print(f'Closed issue: {registered_issue.url}')

		else:
			raise Exception(issue)

	if pending_operations and not read_only:
		file_text, offset = perform_text_operations(file_text, pending_operations)
		with open(filename, 'w') as outfile:
			print(file_text, file=outfile, end='')


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('search_path', type=Path)
	parser.add_argument('-R', '--recursive', action='store_true')
	parser.add_argument('-D', '--dry-run', action='store_true')
	parser.add_argument('-r', '--read-only', action='store_true')
	parser.add_argument('--token-file', type=Path)
	parser.add_argument('--user', type=str)
	parser.add_argument('--repo', type=str)

	args = parser.parse_args()

	if args.recursive:
		glob_gen = args.search_path.glob('**/*.py')
	else:
		glob_gen = args.search_path.glob('*.py')

	if args.dry_run:
		gh = github.dummy_api()
	else:
		if args.token_file:
			gh = github.github_api(token_from_file=args.token_file, user=args.user, repo=args.repo)
		else:
			raise Exception('No token file specified')

	for file in glob_gen:
		print(f'Processing file {file}')
		process_file(file, github_api=gh, read_only=args.read_only)