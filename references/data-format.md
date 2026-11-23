# Resume data format (YAML) and template

`scripts/build_resume.py` turns a YAML file into a .docx using `assets/template.docx`. The model writes the YAML; the script does all layout. See `examples/example_resume.yaml` for a complete file.

## Top level

```yaml
template: en                  # optional: en (default) | zh | path/to/your_template.docx
location_separator: ", "      # optional: text between entry title and location (zh default: full-width space)
header:
  name: Jane Doe
  contact: "email: jane@example.com    Telephone: +1-555-010-0000"   # free text, shown as-is
  # or instead of contact, any of: email, phone, website, linkedin, github
sections:
  - ...   # rendered in this order
```

## Section types

```yaml
# 1) entries (default): title line + italic sub-line(s) + bullets
- title: Research Experience
  style: large              # optional; "large" = 10.5pt sub-lines/bullets (education look). Default = 10pt
  gap_between_entries: true # optional; blank line between entries (default true)
  entries:
    - title: Project or Organization Name
      location: City, ST, USA         # optional; rendered bold-italic after a comma
      date: 01/2026-05/2026           # optional; right-aligned via tab stop
      subtitle: Research Intern       # optional; string or list of strings (one italic line each)
      bullets:
        - Built ...
        - Improved ...

# 2) publications: numbered [1], [2] ...
- title: Publications
  type: publications
  items:
    - "Doe, J., & **Chen, A.** (2025). Title. *Journal Name, 12*, 345. https://doi.org/..."

# 3) bullets: plain bullet list (skills, additional information)
- title: Skills
  type: bullets
  items:
    - "**Programming:** C, C++, Python"

# 4) lines: bold lines with optional right-aligned date (test scores, awards list)
- title: English Proficiency
  type: lines
  items:
    - {title: "IELTS: Overall 7.0", date: 08/2024}
```

## Inline markup (any text field)

`**bold**`, `*italic*`, `***bold italic***`, `^superscript^` (e.g. `3^rd^ Prize`). Quote strings in YAML if they contain `: `, `#`, or start with `*`.

## Keeping a master file

Keep one master YAML with everything the person has ever done. For a targeted version, copy it and delete/reorder, rather than editing the .docx by hand. Put version-specific notes in YAML comments (`# industry version: dropped competitions`).

## Chinese template

`assets/template_zh.docx` is generated from the English one with
`scripts/make_cjk_variant.py assets/template.docx assets/template_zh.docx`. It keeps
the same layout but removes italics (Chinese has no true italic), sets an explicit
East Asian font (等线), grays the location and sub-lines, loosens the exact line
heights by 15% for taller CJK glyphs, and tags text as zh-CN. Use `template: zh`
in the YAML. Run the same script on a custom template to get its Chinese variant.

## Using a different template

The template is a normal .docx whose body contains one prototype paragraph per block type, each containing its marker text:

| Marker | Block |
|---|---|
| `{{SECTION}}` | section heading |
| `{{RULE}}` | paragraph right after a heading (e.g. the one holding a horizontal line); may be an otherwise empty paragraph |
| `{{SPACER}}` | blank line between sections/entries |
| `{{ENTRY_TITLE}}{{ENTRY_LOCATION}}{{ENTRY_TAB}}{{ENTRY_DATE}}` | one paragraph, four runs, each formatted as it should look; the paragraph needs a right tab stop at the text-area edge |
| `{{DEGREE}}` | italic sub-line, large style |
| `{{NOTE}}` | italic sub-line, normal style |
| `{{BULLET_LG}}` | bullet, large style |
| `{{BULLET}}` | bullet, normal style |
| `{{PUB}}` | numbered publication item |

The header holds `{{NAME}}` and `{{CONTACT}}`. Page size, margins and header come from the template's section settings. To make a template from someone's existing resume: copy their .docx, delete everything except one example of each block, replace each block's text with its marker (keep the formatting), add a right tab stop to the title paragraph, and remove any hyperlinks in the header. Then build the example YAML and compare the rendered result with the original side by side.
