# coding=utf-8
import sublime, sublime_plugin, re

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

class MacroKB(object):
	def __init__(self, pat, key):
		self.pat = pat
		self.regex = re.compile(pat)
		self.key = key

class TryExpandMacroKbCommand(sublime_plugin.TextCommand):
	def __init__(self, view):
		self.view = view;
		self.macros = [
				MacroKB(r"\\Downarrow", u"⇓"), 
				MacroKB(r"\\nwarrow", u"↖"), 
				MacroKB(r"\\downarrow", u"↓"), 
				MacroKB(r"\\Rightarrow", u"⇒"), 
				MacroKB(r"\\rightarrow", u"→"), 
				MacroKB(r"\\mapsto", u"↦"), 
				MacroKB(r"\\aleph", u"א"), 
				MacroKB(r"\\prime", u"′"), 
				MacroKB(r"\\emptyset", u"∅"), 
				MacroKB(r"\\sharp", u"♯"), 
				MacroKB(r"\\flat", u"♭"), 
				MacroKB(r"\\neg", u"¬"), 
				MacroKB(r"\\forall", u"∀"), 
				MacroKB(r"\\exists", u"∃"), 
				MacroKB(r"\\infty", u"∞"), 
				MacroKB(r"\\alpha", u"α"), 
				MacroKB(r"\\theta", u"θ"), 
				MacroKB(r"\\tau", u"τ"), 
				MacroKB(r"\\beta", u"β"), 
				MacroKB(r"\\vartheta", u"θ"), 
				MacroKB(r"\\pi", u"π"), 
				MacroKB(r"\\upsilon", u"υ"), 
				MacroKB(r"\\gamma", u"γ"), 
				MacroKB(r"\\lambda", u"λ"), 
				MacroKB(r"\\smiley", u"☺"), 
				MacroKB(r"\\frownie", u"☹")
					  ]
		self.longest_pat = 0
		for mkb in self.macros:
			self.longest_pat = max(len(mkb.pat), self.longest_pat)

	def run(self, edit):
		for r in self.view.sel():
			tsz = min(self.longest_pat, r.b)
			text = self.view.substr(sublime.Region(r.b - tsz, r.b)).encode("utf-8")
			for mac in self.macros:
				m = mac.regex.search(text)
				if m != None:
					start = r.b - tsz
					to_replace = sublime.Region(start + m.start(), start + m.end())
					self.view.replace(edit, to_replace, mac.key)
					break

class InsertLambdaCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		for r in self.view.sel():
			self.view.insert(edit, r.b, u"λ")

class InsertFrownieCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		for r in self.view.sel():
			self.view.insert(edit, r.b, u"☹")

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
			if self.view.substr(matching_brace_pos) == "[":
				self.view.insert(edit, r.b, "]")
			else:
				self.view.insert(edit, r.b, ")")

def scope_for_level(level):
	if level == 0:
		return "sexp.zero"
	elif level == 1:
		return "sexp.one"
	elif level == 2:
		return "sexp.two"
	
	return "sexp.three"

class SExp(object):
	def __init__(self):
		self.level = None
		self.start = None
		self.end = None 
		self.children = []

def peek(ls):
	sz = len(ls)
	if sz == 0:
		return None

	return ls[sz - 1]

class HighlightSExp(sublime_plugin.EventListener):
	def on_selection_modified(self, view):
		view.erase_regions("ParenHighlight0")
		view.erase_regions("ParenHighlight1")
		view.erase_regions("ParenHighlight2")
		view.erase_regions("ParenHighlight3")
		view.erase_regions("ParenHighlight4")
		regions = []
		zeros = []
		ones = []
		twos = []
		threes = []
		fours = []
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


			size = len(text)
			lvl = 0
			p = r.b
			matching_brace_pos = None
			in_str = False
			start_pos_stack = []
			root = None
			exp_stack = []
			for i in range(0, size):
				cur = text[i]
				if cur == '\"':
					if in_str:
						in_str = False
					else:
						in_str = True

				if not in_str:
					if matches(cur, incrs):
						lvl = lvl + 1
						new_sexp = SExp()
						new_sexp.level = lvl
						new_sexp.start = p 

						if root == None:
							root = new_sexp
							exp_stack.append(new_sexp)
						else:
							top = peek(exp_stack)
							top.children.append(new_sexp)

						exp_stack.append(new_sexp)
					elif matches(cur, decrs):
						lvl = lvl - 1
						ended_sexp = exp_stack.pop()
						ended_sexp.end = acc(p) 
						if lvl == 0:
							matching_brace_pos = ended_sexp.end
							break
					
				p = acc(p)

			if matching_brace_pos == None:
				continue

			#Starting at the root, subdivide each node's region 
			#into a list of regions so it doesn't overlap with 
			#its children.  Sublime doesn't appear to be able 
			#to color overlapping regions differently.
			def add_reg(rg, lv):
				if lv == 0:
					zeros.append(rg)
				elif lv == 1:
					ones.append(rg)
				elif lv == 2:
					twos.append(rg)
				elif lv == 3:
					threes.append(rg)
				else:
					fours.append(rg)

			def add_sexp_reg(sexp):
				reg = sublime.Region(sexp.start, sexp.end)
				add_reg(reg, sexp.level)

			def subdivide(node):
				if len(node.children) == 0:
					add_sexp_reg(node)
				else:
					st = node.start 
					for c in node.children:
						add_reg(sublime.Region(st, c.start), node.level)
						subdivide(c)
						st = c.end
					add_reg(sublime.Region(peek(node.children).end, node.end), node.level)

			subdivide(root)
			view.add_regions("ParenHighlight1", ones, "sexp.one", "dot")
			view.add_regions("ParenHighlight2", twos, "sexp.two")
			view.add_regions("ParenHighlight3", threes, "sexp.three")
			view.add_regions("ParenHighlight4", fours, "sexp.four")







