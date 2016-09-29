import re
import sys
import pprint

debug_all = False  # Will override local debug settings.


def translate(text, tags=None):
	t = Translator()
	if tags is not None:
		t.add_tag(*tags)
	return t.translate(text)


class UnbalancedBraces(Exception): pass


def print_cursors(text, *indexes, colors=None):
	color = '\033['+str(";".join(map(str, colors) or []))+';m'
	reset = '\033[0m'
	for i, c in enumerate(text):
		if i in indexes:
			sys.stdout.write(color)
			sys.stdout.write(c)
			sys.stdout.write(reset)
		else:
			sys.stdout.write(c)
	sys.stdout.write('\n')
	sys.stdout.flush()
	if "\n" not in text:
		line = ""
		l = 0
		for c in sorted(indexes):
			line += (c-l)*' '+color+'^'+reset
			l = c + 1
		print(line)


class Translator():

	_include_tags = None

	def __init__(self, **kwargs):
		self._include_tags = list(kwargs.keys())

	def add_tag(self, *tags):
		for tag in tags:
			if tag not in self._include_tags:
				self._include_tags.append(tag)

	def translate(self, text, debug=False):
		tree = self.get_blocks(text, debug=debug)
		if debug_all or debug:
			pp = pprint.PrettyPrinter(indent=4)
			pp.pprint(tree)
		return self.expand_tree(tree)

	def get_blocks(self, text, debug=False):
		output = []
		start, end = self.outer_braces(text)
		if start is not None:
			if start > 0:  # Leading
				leading = self.squash_whitespace(text[0:start])
				if leading != '':
					output += [self.compile_text(leading)]
			output += [self.compile_tag(text[start + 1:end])]
			if len(text) > end + 1:  # Trailing
				trailing = self.squash_whitespace(text[end + 1:])
				if trailing != '':
					output += self.get_blocks(text[end + 1:])
		else:
			output += [self.compile_text(text)]
		return output

	def compile_text(self, text):
		text = self.squash_whitespace(text)
		if text is '':
			return None
		return ("TEXT", text)

	def compile_tag(self, text):
		if re.match(r'^@\w+(\(*.\))?:', text):
			return self.compile_filter(text)
		else:
			return self.compile_branch(text)

	def compile_filter(self, text):
		colon = text.index(':')
		filter_name = text[1:colon]
		start, end = self.outer_braces(filter_name, '(', ')')
		if start is not None:
			params = filter_name[start + 1:end].split('|-')
			filter_name = filter_name[0:start]
		else:
			params = []
		branch = self.compile_branch(text[colon + 2:-1])
		return ('FILTER', filter_name, params, branch)

	def compile_branch(self, text):
		branches = []
		text = self.escape_inner(text)
		clauses = text.split('|-')
		for c in clauses:
			if ':' not in c.strip().split('\n')[0]:
				condition = True
				node = c
			else:
				c = c.lstrip()
				breaker = c.split('\n')[0].index(':')
				condition = self.compile_condition(c[0:breaker])
				node = c[(breaker + 1):]
			node = self.unescape_inner(node)
			branches.append(('WHEN', condition, self.get_blocks(node)))
		return ('BRANCH', branches)

	def compile_condition(self, condition):
		output = []
		conditions = condition.strip().split(';')
		for c in conditions:
			output.append(c.split(','))
		return output

	def outer_braces(_, text, opener='{', closer='}'):
		if opener not in text and closer not in text:
			return (None, None)
		start = None
		openings = 0  # {
		closings = 0  # }
		for cursor, c in enumerate(text):
			if c == opener:
				if openings == 0:
					start = cursor
				openings += 1
			elif c == closer:
				closings += 1
				close = cursor
			if openings > 0 and openings == closings:
				if debug_all:
					print_cursors(text, start, cursor, colors=[1, 96])
				return (start, cursor)
		raise UnbalancedBraces("Unbalanced braces: "+text)

	def _escape(self, text, reverse=False, opener='{', closer='}'):
		syntax_tags = {
			'PIPE': '|',
			'COLON': ':'
		}
		# This regex stuff is ugly and I'll replace it.
		patt = r'(' + re.escape(opener) + r'(.*)' + re.escape(closer) + r')'
		for full, _ in re.findall(patt, text, re.DOTALL):
			subbed = full
			for replacement, c in syntax_tags.items():
				if reverse:
					inner = subbed.replace(replacement, c)
				else:
					inner = subbed.replace(c, replacement)
				subbed = subbed.replace(subbed, inner)
			text = text.replace(full, subbed)
		return text

	def escape_inner(self, text, **kwargs):
		return self._escape(text, **kwargs)

	def unescape_inner(self, text, **kwargs):
		return self._escape(text, reverse=True, **kwargs)

	def expand_node(self, node):
		txt = ""
		if node[0] == "TEXT":
			txt = node[1]
		elif node[0] == "BRANCH":
			txt = self.expand_branch(node)
		elif node[0] == "FILTER":
			txt = self.expand_filter(node)
		else:
			raise ValueError("unknown node type: ", node[0])
		if txt == '':
			return None
		return txt

	def expand_filter(self, node):
		filter_name = node[1]
		params = node[2]
		branch = node[3]
		good = []
		for clause in branch[1]:
			condition = clause[1]
			if type(condition) == bool:
				condition = [condition]
			if self.check_conditions(*condition) is True:
				good.append(self.expand_tree(clause[2]))
		if len(good) == 0:
			return ""
		filter_method = getattr(self, 'filter_' + filter_name, None)
		if filter_method is None:
			raise Exception("Unknown filter: " + filter_name)
		return filter_method(params, good)

	def expand_branch(self, node):
		for clause in node[1]:
			condition = clause[1]
			if type(condition) == bool:
				condition = [condition]
			if self.check_conditions(*condition) is True:
				return self.expand_tree(clause[2])
		return ""

	def expand_tree(self, tree):
		output = []
		words_end = re.compile(r'(\w|[.!?,\(\)\*#])$')
		words_start = re.compile(r'^(\w|[\(\)_\*#])')
		for node in tree:
			text = self.expand_node(node)
			if text is None:
				continue
			if len(output) > 0:
				if words_end.search(output[-1]) and words_start.search(text):
					output.append(' ')
			output.append(text)
		return ''.join(output)

	def check_conditions(self, *conditions):
		if len(conditions) == 1 and conditions[0] == True:
			return True
		match = True
		for c in conditions:
			met = True
			for d in c:
				if d[0] == '!':
					met = not self.condition_met(d[1:])
				else:
					met = self.condition_met(d)
				if not met: break
			match = met
			if match: break
		return match

	def condition_met(self, condition):
		return condition in self._include_tags

	def squash_whitespace(self, text):
		o = []
		punc = ['.', ',', '?', '!']  # English is hard. :(
		lines = [ l.strip() for l in text.split('\n') ]
		# We need two empty lines at the start to constitute a new block
		# because the first empty line happens as a result of indenting.
		if len(lines) > 1 and lines[0] == '':
			if len(lines) > 2 and lines[1] == '':
				o.append('\n\n')
				lines = lines[2:]
			else:
				lines = lines[1:]
		for l in lines:
			if l == '':
				if len(o) == 0 or len(o) > 0 and o[-1] != '\n\n':
					o.append('\n\n')
			elif len(o) > 0 and o[-1] != '\n\n' and l[0] not in punc:
				o.append(' '+l)
			else:
				o.append(l)
		# Same with the end, we need two empty lines because the last
		# linebreak is just indenting.
		if len(o) > 0 and o[-1] == "\n\n":
			if len(lines) > 1 and lines[-2] != "":
				o = o[0:-1]
		output = ''.join(o)
		# Just a bunch of newlines doesn't make a valid block.
		if output.strip() == '':
			return ''
		return output

	def filter_list(self, _, items):
		if len(items) > 1:
			items[-1] = 'and '+items[-1]
		if len(items) > 2:
			return ', '.join(items)
		return ' '.join(items)

	def filter_join(self, args, items):
		return args[0].join(items)
