# coding=utf-8
import sublime, sublime_plugin

def matches(c, cs):
	for ch in cs:
		if c == ch:
			return True

	return False

def find_scope_delim_pos(text, incr_toks, decr_toks, pos=0, level=0):
	if len(text) == 0:
		return 0

	fst = text[0]
	if matches(fst, incr_toks):
		return find_scope_delim_pos(text[1:], incr_toks, decr_toks, pos + 1, level + 1)
	elif matches(fst, decr_toks):
		if level > 1:
			return find_scope_delim_pos(text[1:], incr_toks, decr_toks, pos + 1, level - 1)
		else:
			return pos

	return find_scope_delim_pos(text[1:], incr_toks, decr_toks, pos + 1, level)

def find_scope_delim_pos2(text, incr_toks, decr_toks, pos, accum, terminate_at_level=1, level=0):
	size = len(text)
	lvl = level
	p = pos
	in_str = False
	for i in range(0, size):
		cur = text[i]
		if cur == '\"':
			if in_str:
				in_str = False
			else:
				in_str = True

		if not in_str:
			if matches(cur, incr_toks):
				lvl = lvl + 1
			elif matches(cur, decr_toks):
				lvl = lvl - 1
				if lvl == terminate_at_level:
					return p
			
		p = accum(p)

	return None

def move_to_close_paren(view, extend = False):
	new_sel = []
	sel = view.sel()
	size = view.size()
	for r in sel:
		new_pt = find_scope_delim_pos(view.substr(sublime.Region(r.a, size)), "([", ")]")
		new_pt = new_pt + r.a + 1

		if extend:
			new_sel.append(sublime.Region(r.a, new_pt))
		else:
			new_sel.append(sublime.Region(new_pt))

	sel.clear()
	for r in new_sel:
		sel.add(r)

def move_to_open_paren(view, extend=False):
	new_sel = []
	sel = view.sel()
	size = view.size()
	for r in sel:
		new_pt = find_scope_delim_pos(view.substr(sublime.Region(r.b, 0))[::-1], ")]", "([")
		new_pt = r.b - new_pt - 1
		if extend:
			new_sel.append(sublime.Region(r.a, new_pt))
		else:
			new_sel.append(sublime.Region(new_pt))

	sel.clear()
	for r in new_sel:
		sel.add(r) 

class MoveSexpRightCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		extend = args['extend']
		move_to_close_paren(self.view, extend=extend)

class MoveSexpLeftCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		extend = args['extend']
		move_to_open_paren(self.view, extend=extend)

class InsertLambdaCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		for r in self.view.sel():
			self.view.insert(edit, r.b, u"λ")

class InsertParenCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		for r in self.view.sel():
			matching_brace_pos = find_scope_delim_pos2(
				self.view.substr(sublime.Region(r.b, 0))[::-1], 
				")]",
				"([",
				r.b,
				lambda p: p - 1, 
				terminate_at_level = 0, 
				level = 1) - 1
			print "Character at " + str(matching_brace_pos) + ":" + self.view.substr(matching_brace_pos)
			if self.view.substr(matching_brace_pos) == "[":
				self.view.insert(edit, r.b, "]")
			else:
				self.view.insert(edit, r.b, ")")

class HighlightSExp(sublime_plugin.EventListener):
	def on_selection_modified(self, view):
		view.erase_regions("ParenHighlight")
		regions = []
		for r in view.sel():
			forward = False
			if r.b == 0:
				forward = True
			if not forward:
				if view.substr(r.b) == "(" or view.substr(r.b) == "[":
					forward = True
				elif view.substr(r.b - 1) == ")" or view.substr(r.b - 1) == "]":
					forward = False
				else:
					continue

			size = view.size()
			text = ""
			opens = "(["
			closes = ")]"
			incrs = ""
			decrs = ""
			acc = (lambda p: p + 1) if forward else lambda p: p - 1
			matching_brace_pos = None
			if forward:
				text = view.substr(sublime.Region(r.b, size))
				incrs = opens
				decrs = closes
			else:
				text = view.substr(sublime.Region(r.b, 0))[::-1]
				incrs = closes
				decrs = opens

			matching_brace_pos = find_scope_delim_pos2(
				text, 
				incrs,
				decrs,
				r.b,
				acc,
				terminate_at_level = 0,
				level = 0)

			if matching_brace_pos == None:
				continue

			start = matching_brace_pos + 1
			if not forward:
				start = matching_brace_pos - 1
			end = r.b
			regions.append(sublime.Region(start, end))

		view.add_regions("ParenHighlight", regions, "comment")







