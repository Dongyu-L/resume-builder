#!/usr/bin/env python3
"""Build a .docx resume from a YAML data file using a marker-based Word template.

Usage:
    python build_resume.py resume.yaml output.docx [--template path/to/template.docx]

The template's body holds one prototype paragraph per block type, identified by
a marker text ({{SECTION}}, {{RULE}}, {{SPACER}}, {{ENTRY_TITLE}}..., {{DEGREE}},
{{NOTE}}, {{BULLET_LG}}, {{BULLET}}, {{PUB}}). The header holds {{NAME}} and
{{CONTACT}}. Every generated paragraph is a deep copy of a prototype, so fonts,
spacing, shading, bullets and numbering come from the template, never from code.

Inline markup allowed in any text field:  **bold**   *italic*   ***bold italic***   ^superscript^ (e.g. 3^rd^)
"""
import argparse, copy, os, re, sys
import yaml
import docx
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = os.path.join(HERE, '..', 'assets', 'template.docx')
MARKERS = ['SECTION', 'RULE', 'SPACER', 'ENTRY_TITLE', 'DEGREE', 'NOTE',
           'BULLET_LG', 'BULLET', 'PUB']


def para_text(p):
    return ''.join(t.text or '' for t in p.iter(qn('w:t')))


def load_protos(doc):
    body = doc.element.body
    protos = {}
    for p in body.findall(qn('w:p')):
        m = re.search(r'\{\{([A-Z_]+)\}\}', para_text(p))
        if m:
            key = m.group(1)
            protos[key] = copy.deepcopy(p)
    missing = [k for k in MARKERS if k not in protos]
    if missing:
        sys.exit(f'Template is missing prototype(s): {missing}')
    return protos


def parse_inline(text):
    """Split '**b** *i* ^sup^' markup into [(segment, bold, italic, sup)]."""
    out = []
    pattern = re.compile(r'(\*\*\*.+?\*\*\*|\*\*.+?\*\*|\*.+?\*|\^[^\^\s]+?\^)')
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], None, None, False))
        tok = m.group(0)
        if tok.startswith('***'):
            out.append((tok[3:-3], True, True, False))
        elif tok.startswith('**'):
            out.append((tok[2:-2], True, None, False))
        elif tok.startswith('^'):
            out.append((tok[1:-1], None, None, True))
        else:
            out.append((tok[1:-1], None, True, False))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], None, None, False))
    return out


# Schema order of <w:rPr> children (subset we care about); used for valid insertion.
RPR_ORDER = ['rStyle', 'rFonts', 'b', 'bCs', 'i', 'iCs', 'caps', 'smallCaps', 'strike',
             'dstrike', 'outline', 'shadow', 'emboss', 'imprint', 'noProof', 'snapToGrid',
             'vanish', 'webHidden', 'color', 'spacing', 'w', 'kern', 'position', 'sz', 'szCs',
             'highlight', 'u', 'effect', 'bdr', 'shd', 'fitText', 'vertAlign', 'rtl', 'cs',
             'em', 'lang', 'eastAsianLayout', 'specVanish', 'oMath']


def insert_ordered(rpr, el):
    name = el.tag.split('}')[1]
    rank = RPR_ORDER.index(name)
    for child in rpr:
        cname = child.tag.split('}')[1]
        if cname in RPR_ORDER and RPR_ORDER.index(cname) > rank:
            child.addprevious(el)
            return
    rpr.append(el)


def set_flag(rpr, tag, on):
    for t in (tag, tag + 'Cs'):
        e = rpr.find(qn(t))
        if on and e is None:
            insert_ordered(rpr, rpr.makeelement(qn(t), {}))
        elif on is False and e is not None:
            rpr.remove(e)


def make_runs(template_run, text):
    """Return runs for text with inline markup, cloned from template_run."""
    runs = []
    for seg, b, i, sup in parse_inline(text):
        if not seg:
            continue
        r = copy.deepcopy(template_run)
        rpr = r.find(qn('w:rPr'))
        if rpr is None:
            rpr = r.makeelement(qn('w:rPr'), {})
            r.insert(0, rpr)
        if b is not None:
            set_flag(rpr, 'w:b', b)
        if i is not None:
            set_flag(rpr, 'w:i', i)
        if sup:
            insert_ordered(rpr, rpr.makeelement(qn('w:vertAlign'), {qn('w:val'): 'superscript'}))
        r.find(qn('w:t')).text = seg
        runs.append(r)
    return runs


def keep_with_next(p):
    """Mark a paragraph keepNext so headings/titles never end a page alone."""
    ppr = p.find(qn('w:pPr'))
    if ppr is None:
        ppr = p.makeelement(qn('w:pPr'), {})
        p.insert(0, ppr)
    if ppr.find(qn('w:keepNext')) is not None:
        return
    kn = ppr.makeelement(qn('w:keepNext'), {})
    style = ppr.find(qn('w:pStyle'))
    if style is not None:
        style.addnext(kn)
    else:
        ppr.insert(0, kn)


KEEP_WITH_NEXT = {'SECTION', 'DEGREE', 'NOTE'}


class Builder:
    def __init__(self, template):
        self.doc = docx.Document(template)
        self.protos = load_protos(self.doc)
        body = self.doc.element.body
        self.sect = body.find(qn('w:sectPr'))
        for el in list(body):
            if el is not self.sect:
                body.remove(el)
        self.drawing_id = 1000

    def _emit(self, p):
        self.sect.addprevious(p)
        return p

    def simple(self, key, text):
        """Clone a single-run prototype and fill it with text."""
        p = copy.deepcopy(self.protos[key])
        runs = p.findall(qn('w:r'))
        tmpl = runs[0]
        for r in runs:
            p.remove(r)
        for r in make_runs(tmpl, text):
            p.append(r)
        if key in KEEP_WITH_NEXT:
            keep_with_next(p)
        return self._emit(p)

    def spacer(self):
        p = copy.deepcopy(self.protos['SPACER'])
        for r in p.findall(qn('w:r')):
            p.remove(r)
        self._emit(p)

    def section(self, title):
        self.simple('SECTION', title)
        rule = copy.deepcopy(self.protos['RULE'])
        for r in rule.findall(qn('w:r')):
            if '{{RULE}}' in para_text(r):
                rule.remove(r)
        # drawings need unique ids
        for el in rule.iter():
            if el.tag.endswith('}docPr'):
                self.drawing_id += 1
                el.set('id', str(self.drawing_id))
        keep_with_next(rule)
        self._emit(rule)

    location_separator = ', '

    def entry_title(self, title, location=None, date=None):
        p = copy.deepcopy(self.protos['ENTRY_TITLE'])
        runs = {re.search(r'\{\{(\w+)\}\}', para_text(r)).group(1): r
                for r in p.findall(qn('w:r'))}
        for r in runs.values():
            p.remove(r)
        title_txt = title + (self.location_separator if location else '')
        for r in make_runs(runs['ENTRY_TITLE'], title_txt):
            p.append(r)
        if location:
            for r in make_runs(runs['ENTRY_LOCATION'], location):
                p.append(r)
        if date:
            tab = copy.deepcopy(runs['ENTRY_TAB'])
            t = tab.find(qn('w:t'))
            tab.replace(t, tab.makeelement(qn('w:tab'), {}))
            p.append(tab)
            for r in make_runs(runs['ENTRY_DATE'], str(date)):
                p.append(r)
        keep_with_next(p)
        self._emit(p)

    def set_header(self, name, contact):
        for part in {id(s.header): s.header for s in self.doc.sections}.values():
            for p in part.paragraphs:
                for t in p._p.iter(qn('w:t')):
                    if t.text and '{{NAME}}' in t.text:
                        t.text = t.text.replace('{{NAME}}', name)
                    if t.text and '{{CONTACT}}' in t.text:
                        t.text = t.text.replace('{{CONTACT}}', contact)

    def save(self, path):
        self.doc.save(path)


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


TEMPLATES = {'en': 'template.docx', 'zh': 'template_zh.docx'}


def resolve_template(data, cli_template, data_path):
    if cli_template:
        return cli_template
    t = data.get('template')
    if not t:
        return DEFAULT_TEMPLATE
    if t in TEMPLATES:
        return os.path.join(HERE, '..', 'assets', TEMPLATES[t])
    return t if os.path.isabs(t) else os.path.join(os.path.dirname(os.path.abspath(data_path)), t)


def build(data, template, out):
    validate_data(data)
    b = Builder(template)
    if 'location_separator' in data:
        b.location_separator = data['location_separator']
    elif data.get('template') == 'zh':
        b.location_separator = '\u3000'   # full-width space; the zh template grays the location
    h = data.get('header', {})
    contact = h.get('contact')
    if contact is None:
        parts = [f"{k}: {h[k]}" for k in ('email', 'phone', 'website', 'linkedin', 'github') if h.get(k)]
        contact = '    '.join(parts)
    b.set_header(h.get('name', ''), contact)

    sections = data.get('sections', [])
    for si, sec in enumerate(sections):
        if si > 0:
            b.spacer()
        b.section(sec['title'])
        kind = sec.get('type', 'entries')
        big = sec.get('style') == 'large'  # 10.5pt bullets/sub-lines (education style)
        bullet_key = 'BULLET_LG' if big else 'BULLET'
        if kind == 'publications':
            for item in sec.get('items', []):
                b.simple('PUB', item)
        elif kind == 'bullets':
            for item in sec.get('items', []):
                b.simple('BULLET_LG', item)
        elif kind == 'lines':  # bold line with optional right-aligned date (e.g. test scores)
            for item in sec.get('items', []):
                if isinstance(item, dict):
                    b.entry_title(item.get('title', ''), item.get('location'), item.get('date'))
                else:
                    b.entry_title(item)
        else:
            entries = sec.get('entries', [])
            for ei, e in enumerate(entries):
                if ei > 0 and sec.get('gap_between_entries', True):
                    b.spacer()
                b.entry_title(e['title'], e.get('location'), e.get('date'))
                for line in as_list(e.get('subtitle')):
                    b.simple('DEGREE' if big else 'NOTE', line)
                for bl in as_list(e.get('bullets')):
                    b.simple(bullet_key, bl)
    b.save(out)


def validate_data(data):
    def mapping(value, where):
        if not isinstance(value, dict):
            raise ValueError(f"{where} must be a mapping")
    def text(value, where):
        if not isinstance(value, str):
            raise ValueError(f"{where} must be a string; quote YAML dates and numbers")
    def sequence(value, where):
        if not isinstance(value, list):
            raise ValueError(f"{where} must be a list")
    mapping(data, "resume")
    h = data.get('header', {})
    mapping(h, "header")
    for k, v in h.items():
        text(v, f"header.{k}")
    for k in ('template', 'location_separator'):
        if k in data:
            text(data[k], k)
    sections = data.get('sections', [])
    sequence(sections, 'sections')
    for i, sec in enumerate(sections):
        where = f"sections[{i}]"
        mapping(sec, where)
        text(sec.get('title'), where + '.title')
        kind = sec.get('type', 'entries')
        if kind not in ('entries', 'publications', 'bullets', 'lines'):
            raise ValueError(f"{where}.type is unsupported: {kind}")
        if 'style' in sec and sec['style'] not in ('large', 'normal'):
            raise ValueError(f"{where}.style must be large or normal")
        if 'gap_between_entries' in sec and not isinstance(sec['gap_between_entries'], bool):
            raise ValueError(f"{where}.gap_between_entries must be boolean")
        values = sec.get('entries' if kind == 'entries' else 'items', [])
        sequence(values, where)
        for j, value in enumerate(values):
            loc = f"{where}[{j}]"
            if kind in ('publications', 'bullets') or (kind == 'lines' and isinstance(value, str)):
                text(value, loc)
                continue
            mapping(value, loc)
            text(value.get('title'), loc + '.title')
            for k in ('location', 'date'):
                if k in value:
                    text(value[k], loc + '.' + k)
            for k in ('subtitle', 'bullets'):
                for item in as_list(value.get(k)):
                    text(item, loc + '.' + k)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data')
    ap.add_argument('output')
    ap.add_argument('--template', default=None,
                    help='override the template (default: YAML "template" key, else assets/template.docx)')
    a = ap.parse_args()
    with open(a.data, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    try:
        build(data, resolve_template(data, a.template, a.data), a.output)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    print(f'Wrote {a.output}')


if __name__ == '__main__':
    main()
