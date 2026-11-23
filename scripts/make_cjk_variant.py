#!/usr/bin/env python3
"""Derive a Chinese (CJK) variant of a marker template.

Usage:
    python make_cjk_variant.py template.docx template_zh.docx [--font 等线] [--line-scale 1.15]

Why: Latin-oriented resume templates use italics and tight exact line heights.
Chinese has no true italic (Word just slants the glyphs), and CJK glyphs are
taller, so the same settings look cramped and crooked. This keeps every layout
decision of the original (sizes, shading, rules, bullets, margins, tab stops)
and only changes what CJK text needs:
  * removes italics everywhere (body and header)
  * sets an explicit East Asian font (default 等线, bundled with Office 2016+)
  * renders location and sub-lines in dark gray instead of italic
  * scales every exact line height by --line-scale (default 1.15)
  * turns pattern shading (e.g. pct15) into an equivalent solid gray fill, which
    renders the same in Word and is not dropped by other renderers
"""
import argparse, os, re, shutil, tempfile, zipfile
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
q = lambda t: '{%s}%s' % (W, t)

RPR_ORDER = ['rStyle', 'rFonts', 'b', 'bCs', 'i', 'iCs', 'caps', 'smallCaps', 'strike',
             'dstrike', 'outline', 'shadow', 'emboss', 'imprint', 'noProof', 'snapToGrid',
             'vanish', 'webHidden', 'color', 'spacing', 'w', 'kern', 'position', 'sz', 'szCs',
             'highlight', 'u', 'effect', 'bdr', 'shd', 'fitText', 'vertAlign', 'rtl', 'cs',
             'em', 'lang', 'eastAsianLayout', 'specVanish', 'oMath']
GRAY = '404040'


def insert_ordered(rpr, el):
    rank = RPR_ORDER.index(el.tag.split('}')[1])
    for child in rpr:
        name = child.tag.split('}')[1]
        if name in RPR_ORDER and RPR_ORDER.index(name) > rank:
            child.addprevious(el)
            return
    rpr.append(el)


def fix_rpr(rpr, font, gray=False, unbold=False):
    for tag in ('i', 'iCs'):
        for e in rpr.findall(q(tag)):
            rpr.remove(e)
    if unbold:
        for tag in ('b', 'bCs'):
            for e in rpr.findall(q(tag)):
                rpr.remove(e)
    f = rpr.find(q('rFonts'))
    if f is None:
        f = etree.Element(q('rFonts'))
        insert_ordered(rpr, f)
    for attr in ('eastAsiaTheme',):
        f.attrib.pop(q(attr), None)
    f.set(q('eastAsia'), font)
    lang = rpr.find(q('lang'))
    if lang is not None:
        lang.set(q('eastAsia'), 'zh-CN')   # proper CJK line breaking and justification
    if gray:
        c = rpr.find(q('color'))
        if c is None:
            c = etree.Element(q('color'))
            insert_ordered(rpr, c)
        c.set(q('val'), GRAY)


def solidify_shading(root):
    for shd in root.iter(q('shd')):
        val = shd.get(q('val'), '')
        if val.startswith('pct'):
            pct = int(val[3:] or 0)
            level = round(255 * (1 - pct / 100))
            shd.set(q('val'), 'clear')
            shd.set(q('color'), 'auto')
            shd.set(q('fill'), '%02X%02X%02X' % (level, level, level))


def para_marker(p):
    m = re.search(r'\{\{([A-Z_]+)\}\}', ''.join(p.itertext()))
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--font', default='等线')
    ap.add_argument('--line-scale', type=float, default=1.15)
    a = ap.parse_args()

    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(a.src) as z:
        z.extractall(tmp)

    # body prototypes
    path = os.path.join(tmp, 'word', 'document.xml')
    tree = etree.parse(path)
    for p in tree.iter(q('p')):
        key = para_marker(p)
        for sp in p.iter(q('spacing')):
            if sp.get(q('lineRule')) == 'exact' and sp.get(q('line')):
                sp.set(q('line'), str(round(int(sp.get(q('line'))) * a.line_scale)))
        for r in p.iter(q('r')):
            rpr = r.find(q('rPr'))
            if rpr is None:
                rpr = etree.SubElement(r, q('rPr'))
                r.insert(0, rpr)
            text = ''.join(r.itertext())
            is_loc = '{{ENTRY_LOCATION}}' in text
            gray = is_loc or key in ('DEGREE', 'NOTE')
            fix_rpr(rpr, a.font, gray=gray, unbold=is_loc)
        mark = p.find('w:pPr/w:rPr', NS)
        if mark is not None:
            fix_rpr(mark, a.font)
    solidify_shading(tree.getroot())
    tree.write(path, xml_declaration=True, encoding='UTF-8', standalone=True)

    # headers
    for name in os.listdir(os.path.join(tmp, 'word')):
        if re.match(r'header\d*\.xml$', name):
            hp = os.path.join(tmp, 'word', name)
            ht = etree.parse(hp)
            for rpr in ht.iter(q('rPr')):
                fix_rpr(rpr, a.font)
            ht.write(hp, xml_declaration=True, encoding='UTF-8', standalone=True)

    if os.path.exists(a.dst):
        os.remove(a.dst)
    with zipfile.ZipFile(a.dst, 'w', zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml first, as Word expects
        z.write(os.path.join(tmp, '[Content_Types].xml'), '[Content_Types].xml')
        for root, _, files in os.walk(tmp):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, tmp)
                if rel != '[Content_Types].xml':
                    z.write(full, rel)
    shutil.rmtree(tmp)
    print(f'Wrote {a.dst}')


if __name__ == '__main__':
    main()
