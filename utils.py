import re, dataclasses

class simple_definition:
	def __init__(self, definition, *extra_positionals):
		self.definition = definition
		self.extra_positionals = extra_positionals

class simple_structure(simple_definition):
	def __set_name__(self, target, name):
		setattr(target, name, dataclasses.make_dataclass(name, self.definition.split()))

class simple_pattern(simple_definition):
	#This is nothing fancy, was planning to have named patterns but it was not trivial to extend re patterns to do so
	def __set_name__(self, target, name):
		re_pattern = re.compile(self.definition, *self.extra_positionals)
		setattr(target, name, re_pattern)


def enumerate_pending(source, FINAL=None):
	'''Will yield pairs of consequtive elements, using FINAL for tail

		For the iterable [1, 2, 3] this would output
			1, 2
			2, 3
			3, FINAL

		For the iterable [1] this would output
			1, FINAL

	'''

	item = previous = NOT_SET = object()
	for item in source:
		if previous is not NOT_SET:
			yield previous, item

		previous = item

	if item is not NOT_SET:
		yield item, FINAL


def iter_span(start, stop, size=None, key=None, start_offset=0):

	if key:
		actual_start = key(start) if start is not None else 0
		actual_stop = key(stop) if stop is not None else size
	else:
		actual_start = start if start is not None else 0
		actual_stop = stop if stop is not None else size

	if actual_stop is not None:
		return range(actual_start + start_offset, actual_stop)
	else:
		return ()

