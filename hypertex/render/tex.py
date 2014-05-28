__name__ = "tex"

import os.path
from jinja2 import Environment, PackageLoader

from hypertex.parser import parse_tag, get_number_of_par
from hypertex.constants import BLOCK_TAGS
from hypertex.util import dict_merge

tmpl_env = Environment(loader=PackageLoader("hypertex.render", "tex"))

def _render_content(node, parsed):
  if type(node) is str:
    return node
  content = node.get("content", "")
  if type(content) is list:
    content = "".join(_render_node(n, parsed) for n in content)
  return content

def _render_citation(node, parsed):
  tag = node.get("tag", "")
  ref = node.get("ref", "")
  url = ""
  num = 0
  doc = ""
  text = _render_content(node, parsed)
  if tag:
    (doc, partag) = parse_tag(tag)
    num = get_number_of_par(partag, doc, parsed)
    url = "#"
    if doc:
      url = "%s.pdf#%d" % (doc, num)
    else:
      url = "#%d" % num
  elif ref:
    # TODO
    url = "#%s" % ref

  template = tmpl_env.get_template("citation.tex")
  return template.render({
    "tag":  tag,
    "doc":  doc,
    "num":  str(num),
    "ref":  ref,
    "url":  url,
    "text": text})

def _render_term(node, parsed):
  tag = node.get("tag", "")
  ref = node.get("ref", "")
  url = ""
  num = 0
  doc = ""
  text = _render_content(node, parsed)
  if tag:
    (doc, partag) = parse_tag(tag)
    num = get_number_of_par(partag, doc, parsed)
    url = "#"
    if doc:
      url = "%s.pdf#%d" % (doc, num)
    else:
      url = "#%d" % num
  elif ref:
    # TODO
    url = "#%s" % ref

  template = tmpl_env.get_template("term.tex")
  return template.render({
    "tag":  tag,
    "doc":  doc,
    "num":  str(num),
    "ref":  ref,
    "url":  url,
    "text": text})

def _render_term(node, parsed):
  return _render_content(node, parsed)

def _render_node(node, parsed):
  if type(node) is str:
    return node
  content = _render_content(node, parsed)

  if node.get("type") in BLOCK_TAGS:
    template = tmpl_env.get_template("block.tex")
    return template.render({"block": dict_merge(node, {"content": content})})
  if node.get("type") == "paragraph":
    return "%s\n" % content
  if node.get("type") == "bold":
    return "\\textbf{%s}" % content
  if node.get("type") == "italic":
    return "\\emph{%s}" % content
  if node.get("type") == "definition":
    return "\\emph{%s}" % content
  if node.get("type") == "citation":
    return _render_citation(node, parsed)
  if node.get("type") == "term":
    return _render_term(node, parsed)
  return content

def _render_par(par, parsed):
  return "".join(_render_node(n, parsed) for n in par.get("content"))

def render(parsed):
  template = tmpl_env.get_template("template.tex")
  tex = template.render({
    "title":  parsed["title"],
    "author": parsed["author"],
    "macros": parsed["macros"].items(),
    "pars":   [dict_merge(p, {"content": _render_par(p, parsed)})
                for p in parsed["body"]["pars"]]})
  return tex