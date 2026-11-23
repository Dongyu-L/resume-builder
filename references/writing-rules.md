# Resume writing rules

These rules are shared by both modes: the writer follows them, the reviewer checks against them. Each rule has a reason; when a rule and the user's explicit instruction conflict, follow the user and mention the trade-off once.

## 1. Truthfulness (never break these)

- **Never invent facts.** No made-up metrics, dates, tools, titles, awards, or outcomes. A resume is something the owner must defend line by line in an interview; one fabricated number can sink an offer.
- **Missing data → ask or mark, never fill.** If a bullet would be stronger with a number the user hasn't given, ask for it. If they can't provide it, write the strongest honest version without one, or leave a visible placeholder like `[X%]` and list it in the hand-off message.
- **Don't inflate scope.** "Contributed to" is not "Led"; "under review" is not "accepted"; a course project is not "research". Keep publication status exactly as stated (Under Review / Accepted / In Preparation).
- **Avoid overclaims** a domain reader would doubt: "first ever", "unexplored area", "state-of-the-art" without a benchmark. Prefer "a known challenge", "outperformed [baseline] by X".

## 2. Bullets

- **Start with a strong past-tense action verb** (present tense only for the current role). Rotate verbs; don't open more than ~3 bullets in the whole document with the same one.
  - Build/create: Built, Engineered, Implemented, Developed, Prototyped, Architected
  - Improve: Optimized, Accelerated, Reduced, Improved, Streamlined, Refactored
  - Lead: Led, Coordinated, Mentored, Directed, Initiated
  - Research: Investigated, Proposed, Formulated, Validated, Benchmarked, Evaluated
  - Weak openers to avoid: Responsible for, Helped, Worked on, Participated in, Was involved in.
- **Formula:** action + what/how (method, tools) + result (number, comparison, outcome). Not every bullet needs a number, but every entry should have at least one quantified bullet if the facts allow.
- **Length:** aim for 1–2 lines; 3 lines is the ceiling. Split long bullets rather than cramming.
- **One idea per bullet.** Don't join unrelated achievements with "Additionally,".
- **Numbers:** use digits (5 m/s, 18 ms, 60%), keep units consistent, and give the baseline when stating improvements ("from 75.8% to 80.7%", "+67%").
- **Specific > generic.** "YOLOv12s with depth-feature fusion" beats "a deep learning model". Name datasets, hardware (STM32F407), frameworks (PyTorch, MONAI).
- **No first person** (I, my, we), no filler (successfully, various, etc., in order to → to).
- End bullets consistently: either all with a period or none. Default: with a period.

## 3. Entries and sections

- **Reverse chronological** within each section (most recent first). Education included.
- **Dates:** one format throughout. Default `MM/YYYY-MM/YYYY`, ongoing as `MM/YYYY-Present`. Test dates may use the same `MM/YYYY`.
- **Locations:** US → `City, ST, USA` (East Lansing, MI, USA). Elsewhere → `City, Country` (Jinan, China).
- **Entry title line:** organization/project name, location (if applicable), right-aligned date. Role/degree/award goes on the italic line below.
- **Every job entry needs a role title** (e.g. "Research Intern") under the organization.
- **Grades:** for a US audience use GPA on the school's scale (3.9/4.0). A non-US percentage can stay, optionally with the scale.
- **Publications:** consistent citation style (default APA-like as in the template), owner's name in bold, status in parentheses for unpublished work, DOI when available.
- **Skills section:** group by category (Programming / ML & CV / Embedded & Hardware / Tools / Languages). Don't list years of experience per language unless asked. Don't list skills never evidenced elsewhere unless the user insists.
- **Language proficiency** sections (IELTS/TOEFL) are for applications that require them; for someone already studying or working in an English-speaking country, suggest removing.

## 4. Tailoring (when a job description or target is given)

- Mirror the JD's key terms where they are true for the user (ATS keyword match).
- Reorder bullets so the most relevant come first; reorder entries only within reverse-chronological constraints, or move a whole section up.
- Cut or compress the least relevant entries before shrinking font or margins.
- Targets:
  - **Academic CV** (PhD applications, fellowships, faculty): length is fine; publications near the top; include all research.
  - **Industry resume** (internships, jobs): 1 page for < 5 years of experience, 2 pages max for PhD; lead with skills/experience most relevant to the role; compress competitions and coursework.

## 5. English quality

- US spelling by default (optimize, modeling, center).
- Hyphenate compound modifiers ("real-time control", "point-cloud-free"), not predicates.
- Title case for entry titles; sentence case for bullets.
- Watch for Chinese-English patterns: "realize" (→ achieve/enable), "put into use" (→ deploy), "gain information" (→ obtain/estimate), "participated" without "in", missing articles, "a patent named …" (→ "Patent: …").

## 6. Chinese resumes (中文简历)

Write Chinese that reads as if a native speaker wrote it first, not a translation of the English version. Translate meaning, not sentence structure.

- **Verb-first, compact clauses.** 搭建、设计、实现、提出、负责、主导、优化. Split long English sentences into two short clauses joined by "，" or "；" rather than one long 定语 chain.
- **Avoid translationese:**
  - "进行了……的……" / "对……进行……" → use the verb directly (进行了优化 → 优化)
  - "被用于" → "用于"; "使得……能够" → "使……"; "一个/一种" before every noun → drop
  - English participial tails ("…, achieving X") → a separate clause ("……，准确率达 X")
  - "独立的""有效的" and other filler adjectives → drop unless they carry information
- **Results read naturally:** "mAP50 由 75.8% 提升至 80.7%", "速度提升 60%", "误差不超过 0.5 m", "比基线快 3 倍".
- **Typography:** full-width punctuation (，。：；（）“”) around Chinese text; a half-width space between Chinese and English words or numbers (基于 Python 开发, 7 个电机); units keep a space (5 m/s, 2.64 cm).
- **Dates:** `YYYY.MM-YYYY.MM`, ongoing `YYYY.MM-至今`.
- **Names must match official documents.** Company names, competition names and levels, program names (e.g. 卓越工程师计划), patent titles: ask for the exact Chinese wording. Never guess a company's Chinese name; leave a visible placeholder and ask.
- **Keep in English:** publication citations, English-only proper nouns (model names, datasets, software), and the English company name in parentheses when the Chinese name is less recognizable.
- **Layout:** use the `zh` template (no italics; gray sub-lines; slightly taller line height). Don't reuse the English template for Chinese text.
