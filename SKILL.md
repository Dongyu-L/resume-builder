---
name: resume-builder
description: Write, tailor, and review English and Chinese resumes or academic CVs using YAML and Word templates. Use for resume creation, updates, job-specific tailoring, or resume feedback; preserve a user-requested format when supplied.
---

# Resume builder

Two modes that share one rulebook:

- **Write mode**: facts in → a .docx out, in the template's exact format.
- **Review mode**: a resume in → a prioritized list of problems and fixes (optionally as Word comments).

Use the bundled layout unless the user provides or requests another format. The model writes content as YAML; `scripts/build_resume.py` clones formatted prototype paragraphs from `assets/template.docx`. This preserves template formatting; pagination still depends on content, fonts, and renderer. Don't hand-edit XML or use docx-js to "recreate" the look.

Files:
- `references/writing-rules.md`: what good content looks like. **Read it before writing or reviewing anything.**
- `references/review-checklist.md`: judgement checklist and report format for review mode.
- `references/data-format.md`: YAML schema, inline markup, how to use another template.
- `examples/example_resume.yaml`: a complete fictional example.
- `scripts/build_resume.py`, `scripts/check_resume.py`, `scripts/render_preview.py`.
- `assets/template_zh.docx` + `scripts/make_cjk_variant.py`: Chinese template and the script that derives it from any template.

Dependencies: Python 3.10+ and `requirements.txt`; LibreOffice (`soffice`) and Poppler (`pdfinfo`, `pdftoppm`) for previews and page counts. Pandoc is optional for DOCX text extraction. Resolve script paths relative to this skill directory; keep user data and outputs in the user workspace, not the installed skill directory.

Talk to the user in the language they use; write resume content in the resume's language (usually English).

---

## Write mode

Use for: a new resume, a new version of an existing one, adding material, tailoring to a job.

### 1. Gather the source of truth
- If the user has an existing resume (.docx/.pdf), read it with available document/PDF tools (optional for DOCX: `pandoc -t markdown file.docx`) and convert it into YAML faithfully first: same entries, same wording. This is the baseline; every later change is a diff against it.
- If a master YAML exists from earlier work, start from that instead.
- Collect the new material and instructions. Note the **target** (academic CV vs industry resume vs a specific JD) and **page limit**; ask if unclear, since they change what gets cut.

### 2. Ask before writing
Before drafting, list what's missing or ambiguous and ask, in one compact message:
- numbers that would make a bullet concrete (accuracy, speed-up, dataset size, latency, team size)
- role titles, exact dates, locations, publication status
- anything that conflicts with the existing resume

Ask only questions that materially change the output; use facts already available in the conversation. If the user says to go ahead without answers, use honest wording and `[placeholder]`s for missing numbers. Never invent a figure.

### 3. Draft the YAML
- Apply `references/writing-rules.md`.
- When polishing an existing resume, respect the requested degree of change. "Don't change much" means: fix errors, tighten wording, add quantification where the user gave numbers, keep structure and most sentences. Keep a list of every substantive change for the hand-off.
- Keep the owner's name bold in publications (`**Granger, H.**`).

### 4. Build, check, look
```bash
mkdir -p outputs
python3 scripts/build_resume.py resume.yaml outputs/resume.docx
python3 scripts/check_resume.py outputs/resume.docx --max-pages 2
python3 scripts/render_preview.py outputs/resume.docx outputs/preview
```
Open the page images and actually look: awkward line breaks (one or two words alone on a line), a heading stranded at the bottom of a page, page overflow. Fix in the YAML (tighten a bullet, move a line) and rebuild. Resolve every check_resume finding or consciously accept it (e.g. a date from a test certificate).

### 5. Hand off
Deliver the .docx (and keep the YAML alongside it so the next version starts from data, not from Word). In the message: a short list of what changed and why, any placeholders the user must fill, and any facts you were unsure about. Don't repeat the whole resume in chat.

---

## Review mode

Use for: "analyze / check / critique my resume", "what's wrong with this", "how does this fit this JD".

1. Read `references/writing-rules.md` and `references/review-checklist.md`.
2. Run `python3 scripts/check_resume.py <file> [--max-pages N]` for mechanical issues (for a PDF, convert or read the text and do those checks by eye).
3. Read the content (`pandoc -t markdown`) and render it (`render_preview.py`) to see what a reader sees.
4. Go through the checklist; if a JD was given, do section E.
5. Write the report in the checklist's format: Overall → Must fix → Should improve (original → rewrite) → Optional → Questions.

Don't rewrite the whole resume in review mode unless asked; offer to produce the revised version (write mode) at the end.

### Annotated output (optional)
If the user requests Word comments or tracked changes, use available document-editing tools or a compatible document skill. These features are not implemented by this repository. If unavailable, deliver a Markdown review and explain the limitation; do not claim to have added comments or tracked changes.

---

## Bilingual versions (e.g. English + 中文)

- Keep one YAML per language (`<Name>_CV_V7.yaml`, `<中文名>_简历_V7.yaml`) with identical structure, so an edit in one is easy to mirror in the other.
- If the user edited the English .docx by hand, read it back first and carry their edits into both YAML files before generating the other language.
- Chinese: set `template: zh`, follow `references/writing-rules.md` §6, and write natural Chinese rather than translating sentence by sentence. List every proper name you were unsure of (company, competition, program, patent title) and ask; never guess.
- Chinese text runs longer vertically; if the page count grows, trim wording before touching layout.
- LibreOffice previews may not draw the gray heading background behind Chinese text, and may justify mixed bold/Chinese lines unevenly; Rendering varies by application and installed fonts. Inspect the available preview, report unresolved differences, and avoid changing the source solely to compensate for one renderer.

## Common judgement calls

- **Multiple versions** (academic vs industry, different JDs): one master YAML, one derived YAML per version. Name outputs `<Name>_CV_<target>_V<n>.docx`.
- **Too long**: cut in this order: redundant bullets → oldest/least relevant entries → merge similar entries (e.g. two competitions) → shorten bullets. Change the template's font or margins only if the user asks.
- **Weak entry with no numbers**: ask for one real metric; if none exists, make the method and the owner's role specific instead.
- **Owner insists on something against the rules** (e.g. keep IELTS): do it, mention the trade-off once, move on.

## Privacy and check limitations

Keep private resume YAML and generated files out of the public repository. Before sharing a custom template, inspect document properties, comments, revisions, hyperlinks, and embedded content. The bundled templates contain fictional markers and have been stripped of custom and personal core properties.

The checker is heuristic: it primarily examines body paragraphs and directly numbered lists, not all tables or inherited formatting. Missing dependencies must be reported as skipped checks. Do not treat a clean report as factual verification or ATS certification.

If CJK characters render as boxes or disappear, check installed fonts and the renderer’s font discovery before changing document content. Fontconfig-based builds may require `FONTCONFIG_FILE` with system font directories and a CJK fallback. See README font guidance.
