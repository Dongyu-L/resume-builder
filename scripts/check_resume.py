#!/usr/bin/env python3
"""Mechanical checks for a .docx resume. Prints a Markdown report.

Usage:
    python check_resume.py resume.docx [--max-pages N]

Catches the objective problems a human reviewer notices but a language model
tends to skim over: inconsistent date formats, non-reverse-chronological order,
alignment done with spaces, mismatched bullet symbols, stale contact links,
spacing/punctuation slips, overlong bullets, and bullets with no numbers.
Content judgement (impact, wording, fit to a job) is left to the model.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile, zipfile
from collections import Counter, defaultdict
import docx
from docx.oxml.ns import qn

MONTHS = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec'
_D = rf'(?:(?:\d{{1,2}}/)?\d{{4}}(?:\.\d{{1,2}})?|(?:\d{{1,2}} )?(?:{MONTHS})[a-z]*\.? ?\d{{4}})'
DATE_TOKEN = re.compile(
    rf'({_D})(?:\s*[-–—~至]+\s*({_D}|Present|Now|Current|至今|今))?\s*$', re.I)
WEAK_OPENERS = ['responsible for', 'helped', 'worked on', 'participated in', 'assisted',
                'involved in', 'was ', 'did ', 'tried']
COMMON_TYPOS = {
    'natioanl': 'national', 'recieve': 'receive', 'seperate': 'separate',
    'occured': 'occurred', 'acheive': 'achieve', 'enviroment': 'environment',
    'managment': 'management', 'developement': 'development', 'expirience': 'experience',
    'algorithim': 'algorithm', 'preformance': 'performance', 'accurracy': 'accuracy',
    'iteration closest point': 'iterative closest point', 'teh': 'the',
}


def page_count(path):
    exe = shutil.which('soffice') or shutil.which('libreoffice')
    if not exe or not shutil.which('pdfinfo'):
        return None
    try:
        with tempfile.TemporaryDirectory(prefix='resume-check-') as out:
            from pathlib import Path
            profile = (Path(out) / 'profile').as_uri()
            subprocess.run([exe, f'-env:UserInstallation={profile}', '--headless',
                            '--convert-to', 'pdf', '--outdir', out, os.path.abspath(path)],
                           capture_output=True, check=True, timeout=180)
            pdf = os.path.join(out, os.path.splitext(os.path.basename(path))[0] + '.pdf')
            info = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True,
                                  check=True, timeout=30).stdout
            match = re.search(r'Pages:\s+(\d+)', info)
            return int(match.group(1)) if match else None
    except (OSError, subprocess.SubprocessError):
        return None


def numbering_map(doc):
    """numId -> (lvlText, font, indent) for level 0."""
    res = {}
    try:
        numbering = doc.part.numbering_part.element
    except Exception:
        return res
    absmap = {}
    for a in numbering.findall(qn('w:abstractNum')):
        lvl = a.find(qn('w:lvl'))
        if lvl is None:
            continue
        txt = lvl.find(qn('w:lvlText'))
        fmt = lvl.find(qn('w:numFmt'))
        fonts = lvl.find('.//' + qn('w:rFonts'))
        ind = lvl.find('.//' + qn('w:ind'))
        absmap[a.get(qn('w:abstractNumId'))] = (
            txt.get(qn('w:val')) if txt is not None else '',
            fmt.get(qn('w:val')) if fmt is not None else '',
            fonts.get(qn('w:ascii')) if fonts is not None else '',
            ind.get(qn('w:left')) if ind is not None else '')
    for n in numbering.findall(qn('w:num')):
        aid = n.find(qn('w:abstractNumId')).get(qn('w:val'))
        res[n.get(qn('w:numId'))] = absmap.get(aid)
    return res


def end_key(date_str):
    """Sortable (year, month) for the END of a date range; Present = far future."""
    if re.search(r'present|now|current|至今|今$', date_str, re.I):
        return (9999, 12)
    named = re.findall(r'(?i)(' + MONTHS + r')[a-z]*\.?\s+(\d{4})', date_str)
    if named:
        month, year = named[-1]
        names = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        return (int(year), names.index(month[:3].lower()) + 1)
    toks = re.findall(r'(?:(\d{1,2})/)?(\d{4})(?:\.(\d{1,2}))?', date_str)
    if not toks:
        return None
    m, y, m2 = toks[-1]
    month = m or m2
    return (int(y), int(month) if month else 12)


def date_shape(s):
    parts = re.split(r'\s*[-–—]+\s*', s)
    if len(parts) == 2 and re.fullmatch(r'(?i)present|now|current|至今|今', parts[1].strip()):
        s = parts[0] + '-' + parts[0]   # "MM/YYYY-Present" has the same shape as "MM/YYYY-MM/YYYY"
    s = re.sub(r'\d', '9', s)
    s = re.sub(rf'(?i)\b({MONTHS})[a-z]*', 'Mon', s)
    return re.sub(r'\s+', ' ', s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx')
    ap.add_argument('--max-pages', type=int, default=None)
    a = ap.parse_args()

    doc = docx.Document(a.docx)
    nummap = numbering_map(doc)
    paras = doc.paragraphs
    issues = defaultdict(list)

    def snip(t, n=70):
        t = t.strip()
        return t if len(t) <= n else t[:n] + '…'

    # --- page count
    pages = page_count(a.docx)
    if pages is not None and a.max_pages and pages > a.max_pages:
        issues['Length'].append(f'{pages} pages; target is {a.max_pages}.')

    # --- walk paragraphs
    section = None
    entries_by_section = defaultdict(list)   # section -> [(idx, date, key)]
    date_shapes = Counter()
    bullet_styles = defaultdict(list)       # (symbol, font, indent, boldmark) -> [idx]
    bullets = []                              # (idx, text, entry)
    current_entry = None

    for i, p in enumerate(paras):
        text = p.text
        stripped = text.strip()
        if not stripped:
            continue
        ppr = p._p.pPr
        numpr = ppr.numPr if ppr is not None else None
        is_list = numpr is not None and numpr.numId is not None
        runs = p.runs
        all_bold = runs and all((r.bold or (r.style and r.style.font.bold)) for r in runs if r.text.strip())

        # section heading: short, bold, no date, not a list, shaded or followed by a rule
        shd = p._p.find('.//' + qn('w:shd'))
        if not is_list and len(stripped) < 45 and (shd is not None) and not DATE_TOKEN.search(stripped):
            section = stripped
            current_entry = None
            continue

        # alignment by spaces
        if re.search(r'\S {5,}\S', text):
            issues['Layout'].append(f'¶{i} “{snip(stripped, 50)}”: date/right text aligned with a run of spaces; use a right tab stop instead (breaks when fonts change).')

        # entry title with date at end
        m = DATE_TOKEN.search(stripped)
        if not is_list and m and len(stripped) > len(m.group(0)) + 3:
            date = m.group(0).strip()
            date_shapes[date_shape(date)] += 1
            entries_by_section[section].append((i, date, end_key(date), snip(stripped[:len(stripped) - len(m.group(0))].strip(), 45)))
            current_entry = snip(stripped[:len(stripped) - len(m.group(0))].strip(), 45)
            if re.search(r'\bAmerica\b', stripped):
                issues['Wording'].append(f'¶{i} “{current_entry}”: write US locations as “City, ST, USA” rather than “…, America”.')
            continue

        if is_list:
            nid = numpr.numId.val
            info = nummap.get(str(nid))
            if info and info[1] == 'bullet':
                mark = ppr.find(qn('w:rPr'))
                boldmark = mark is not None and mark.find(qn('w:b')) is not None
                bullet_styles[(info[0], info[2], info[3], boldmark)].append(i)
                bullets.append((i, stripped, current_entry, section))

        # text-level checks for every non-empty paragraph
        low = stripped.lower()
        for bad, good in COMMON_TYPOS.items():
            if re.search(r'\b' + re.escape(bad), low):
                issues['Spelling'].append(f'¶{i}: “{bad}” → “{good}”.')
        if re.search(r'[A-Za-z]:[A-Za-z]', stripped) and 'http' not in stripped:
            issues['Punctuation'].append(f'¶{i} “{snip(stripped, 50)}”: missing space after colon.')
        if re.search(r'[A-Za-z],[A-Za-z]', stripped) and 'http' not in stripped:
            issues['Punctuation'].append(f'¶{i} “{snip(stripped, 50)}”: missing space after comma.')
        if re.search(r'\S {2,}\S', text) and not re.search(r'\S {5,}\S', text):
            issues['Punctuation'].append(f'¶{i} “{snip(stripped, 50)}”: double space.')
        if re.search(r'\(\s|\s\)', stripped):
            issues['Punctuation'].append(f'¶{i} “{snip(stripped, 50)}”: space just inside parentheses.')

    # --- date format consistency
    if len(date_shapes) > 1:
        shapes = ', '.join(f'“{s}”×{n}' for s, n in date_shapes.most_common())
        issues['Dates'].append(f'Mixed date formats: {shapes}. Pick one (e.g. MM/YYYY-MM/YYYY).')

    # --- reverse chronological order
    for sec, ents in entries_by_section.items():
        keys = [e for e in ents if e[2]]
        for (i1, d1, k1, t1), (i2, d2, k2, t2) in zip(keys, keys[1:]):
            if k2 > k1:
                issues['Order'].append(f'“{sec}”: “{t2}” ({d2}) ends later than “{t1}” ({d1}) but is listed after it; US resumes are reverse-chronological.')
                break

    # --- bullet symbol consistency
    if len(bullet_styles) > 1:
        common = max(bullet_styles, key=lambda k: len(bullet_styles[k]))
        for k, idxs in bullet_styles.items():
            if k == common:
                continue
            diff = []
            if k[0] != common[0] or k[1] != common[1]:
                diff.append('different bullet glyph/font')
            if k[2] != common[2]:
                diff.append(f'indent {k[2]} vs {common[2]}')
            if k[3] != common[3]:
                diff.append('bold paragraph mark (bullet renders heavier)' if k[3] else 'non-bold paragraph mark')
            issues['Layout'].append(f'Bullets at ¶{", ¶".join(map(str, idxs))}: {"; ".join(diff)} compared with the rest.')

    # --- bullet content checks
    firsts = Counter()
    per_entry = defaultdict(lambda: [0, 0])
    for i, t, ent, sec in bullets:
        if sec and re.search(r'educat|skill|additional|language|honor|award|教育|技能|语言|荣誉|奖项', sec, re.I):
            continue
        low = t.lower()
        for w in WEAK_OPENERS:
            if low.startswith(w):
                issues['Wording'].append(f'¶{i}: weak opener “{t.split()[0]} …”; start with a strong action verb.')
                break
        if t[0].islower():
            issues['Wording'].append(f'¶{i}: bullet starts lowercase (“{snip(t, 30)}”).')
        if len(t) > 260:
            issues['Length'].append(f'¶{i}: bullet is {len(t)} characters (≈3+ lines); split or tighten.')
        firsts[t.split()[0].lower()] += 1
        if ent:
            per_entry[ent][0] += 1
            if re.search(r'\d', t):
                per_entry[ent][1] += 1
    for verb, n in firsts.items():
        if n >= 4:
            issues['Wording'].append(f'“{verb.capitalize()}” opens {n} bullets; vary the verbs.')
    for ent, (n, q) in per_entry.items():
        if n >= 2 and q == 0:
            issues['Impact'].append(f'“{ent}”: none of its {n} bullets contain a number (metric, scale, speed-up, dataset size…).')

    # --- hyperlinks (incl. header) whose target disagrees with the visible text
    with zipfile.ZipFile(a.docx) as z:
        for name in z.namelist():
            if re.match(r'word/(document|header\d*|footer\d*)\.xml$', name):
                rels_name = name.replace('word/', 'word/_rels/') + '.rels'
                if rels_name not in z.namelist():
                    continue
                rels = z.read(rels_name).decode('utf8')
                xml = z.read(name).decode('utf8')
                plain = re.sub(r'<[^>]+>', '', xml)
                digits_in_text = re.sub(r'\D', '', plain)
                for rid, target in re.findall(r'Id="(rId\d+)"[^>]*Target="((?:tel|Tel|TEL|mailto):[^"]+)"', rels):
                    if f'r:id="{rid}"' not in xml:
                        continue
                    if target.lower().startswith('tel:'):
                        num = re.sub(r'\D', '', target)
                        if num and num not in digits_in_text:
                            issues['Contact'].append(f'{name}: a phone hyperlink points to {target}, which does not match the number shown. Clicking it dials the wrong number.')
                    else:
                        addr = target.split(':', 1)[1]
                        if addr.lower() not in plain.lower():
                            issues['Contact'].append(f'{name}: an email hyperlink points to {addr}, which is not the address shown.')

    # --- report
    print(f'# Mechanical check: {os.path.basename(a.docx)}')
    if pages is not None:
        print(f'Pages: {pages}')
    else:
        print('Page count: SKIPPED (LibreOffice/pdfinfo unavailable or conversion failed).')
    if not issues:
        print('\nNo mechanical issues found.')
        return
    order = ['Contact', 'Spelling', 'Order', 'Dates', 'Layout', 'Punctuation', 'Impact', 'Wording', 'Length']
    for cat in order + [c for c in issues if c not in order]:
        if cat in issues:
            print(f'\n## {cat}')
            for msg in dict.fromkeys(issues[cat]):
                print(f'- {msg}')


if __name__ == '__main__':
    main()
