import sys
import os.path
from functools import reduce
from lxml import etree
from jinja2 import Environment, FileSystemLoader

_para_types = ["intro", "para", "def", "rmk", "lem", "prp", "thm", "cor", "prf"]

def _dict_merge(d, e):
  return dict(list(d.items()) + list(e.items()))

def _parse_head(head):
  title = head.find("title")
  author = head.find("author")
  return {"title":  title.text if title is not None else "",
          "author": author.text if author is not None else "",
          "macros": dict([(x.attrib.get("name"), x.attrib.get("value"))
                      for x in head.findall("macro")])}

def _parse_node(element):
  a = {"content": ([element.text] if element.text else []) + sum([[_parse_node(child), child.tail or ""] for child in element], [])}
  if element.tag == "b":
    a["type"] = "bold"
  elif element.tag == "i":
    a["type"] = "italic"
  elif element.tag == "u":
    a["type"] = "underline"
  elif element.tag == "d":
    a["type"] = "definition"
  elif element.tag == "cite":
    a["type"] = "citation"
    a["ref"] = element.attrib.get("ref")
    a["tag"] = element.attrib.get("tag")
  return a

def _parse_body_paras(paras, element):
  if element.tag in _para_types:
    return paras + [{
      "type":    element.tag,
      "content": [_parse_node(element)],
      "tags":    element.attrib.get("tag", "").split(";")}]
  return paras

def _parse_body(body):
  return {"body": {"paras": reduce(_parse_body_paras, body, [])}}

def _parse_first_gen(parsed, element):
  if element.tag == "head":
    return _dict_merge(parsed, _parse_head(element))
  if element.tag == "body":
    return _dict_merge(parsed, _parse_body(element))
  return parsed

def parse_texml(input):
  root = etree.fromstring(input)
  return reduce(_parse_first_gen, root, {})

def _render_node_to_html(node):
  if type(node) is str:
    return node
  content = node.get("content", "")
  if type(content) is list:
    content = "".join(_render_node_to_html(n) for n in content)
  if node.get("type") in _para_types:
    return "<div class=\"para %s\">1.&nbsp;&nbsp;%s</div>" % (node.get("type"), content)
  if node.get("type") == "bold":
    return "<b>%s</b>" % content
  if node.get("type") == "italic":
    return "<i>%s</i>" % content
  if node.get("type") == "definition":
    return "<span class=\"definition\">%s</span>" % content
  if node.get("type") == "citation":
    return "<span class=\"citation\">%s</span>" % content
  return content

def _render_para_to_html(para):
  return "".join(_render_node_to_html(n) for n in para.get("content"))

def _render_content_to_html(parsed):
  return "\n".join(_render_node_to_html(para) for para in parsed["body"]["paras"])

def _escape_macros(macros):
  return [(k, v.replace("\\", "\\\\")) for (k, v) in macros.items()]

def texml_to_html(input):
  parsed = parse_texml(input)

  env = Environment(loader=FileSystemLoader("./"))
  template = env.get_template("template.html")
  html = template.render({
    "title":   parsed["title"],
    "author":  parsed["author"],
    "macros":  _escape_macros(parsed["macros"]),
    "paras":   [_dict_merge(p, {"content": _render_para_to_html(p)}) for p in parsed["body"]["paras"]]})
  return html

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("Please specify input texml file.")
    exit()
  infile = sys.argv[1]
  try:
    input = open(infile, "r").read()
  except IOError:
    print("Unable to open the file: %s" % infile)
    exit()
  outfile = os.path.splitext(infile)[0] + ".html"
  try:
    open(outfile, "w").write(texml_to_html(input))
  except IOError:
    print("Unable to write to file: %s" % outfile)
