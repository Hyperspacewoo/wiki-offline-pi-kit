# Public-Release Compliance Memo (Risk Guidance, Not Legal Advice)

_Last updated: 2026-03-24_

> **Important:** This memo is practical risk guidance for launch prep, **not legal advice**. For high-confidence public release decisions, get review from qualified counsel.

## 1) Executive Summary

For this offline knowledge kit, the main pre-launch compliance risks are:

1. **Content licensing/attribution drift** (especially bundled ZIMs)  
2. **Insufficient medical/safety disclaimers** (first-aid, water treatment, shelter guidance)  
3. **Missing minimum public policies** (takedown/contact + trademark/affiliation language)

If you do only a minimum viable compliance pass before launch, do these first:

- Publish a clear **Third-Party Content & Licenses** notice
- Add prominent **Safety + Medical + No-Warranty** disclaimers in README and in-app UI
- Add a lightweight **Takedown/Correction policy + contact email**
- Add **trademark/non-affiliation language** for third-party marks (Wikipedia, OpenStreetMap, Stack Overflow, Kiwix)

---

## 2) Bundled ZIM Redistribution: Practical Implications

## Known bundled files (current repo)

- `zims/Wikipedia.zim`
- `zims/WikiMedicine.zim`
- `zims/OpenStreetMap.zim`
- `zims/StackOverFlow.zim`

Because ZIM is a container format, obligations come from **upstream content licenses**, not from “.zim” itself.

## Working license map (verify before public shipment)

| ZIM | Likely upstream license family | Main obligations to satisfy in your distribution |
|---|---|---|
| Wikipedia | CC BY-SA (plus historical GFDL context on some content) | Attribution, link/reference to license, indicate modifications, preserve share-alike obligations where applicable |
| WikiMedicine | Likely CC BY-SA-family medical wiki content | Same as above + strong medical disclaimer (safety risk) |
| OpenStreetMap | ODbL 1.0 data | Visible attribution to OpenStreetMap contributors + license notice + share-alike/database obligations when distributing derivative DBs |
| StackOverFlow | CC BY-SA (version depends on contribution date) | Attribution to source + author attribution expectations + share-alike for adapted content |

### Key risk note
File names alone are not sufficient evidence for final legal sign-off. Before launch, generate a per-file metadata manifest (title/source/license/version/date) and keep it with the release.

---

## 3) Safety / Liability-Sensitive Content (First Aid, Water, Shelter)

The kit includes potentially life-critical information. You should treat this as a **high-severity user-harm risk area**.

### Minimum disclaimer outcomes

1. **Not medical/professional advice**
2. **Emergency escalation language** (call local emergency services/poison center when needed)
3. **No warranty of completeness/accuracy/currentness**
4. **Local standards override** (codes, regulations, clinical guidance vary)
5. **User responsibility statement** for use under hazardous conditions

Make this visible in at least 3 places:
- README / docs
- In-app first-run notice (or modal)
- Footer notice on relevant pages (medical, water, shelter)

---

## 4) Minimum Policy/Docs to Add Before Public Launch

## P0 (must-have before public release)

1. **Third-Party Content & License Notice** (`docs/THIRD_PARTY_CONTENT_NOTICE.md`)
   - list each bundled dataset/content source
   - applicable license and canonical license URL
   - attribution text required by each source

2. **Safety & Medical Disclaimer** (`docs/SAFETY_AND_MEDICAL_DISCLAIMER.md`)
   - plain-language, high-visibility warning
   - emergency escalation instructions
   - no warranty/no liability framing

3. **README public disclaimer block**
   - short version linked to full disclaimer docs

4. **In-app notice text**
   - shown at first launch and on safety-critical sections

5. **Takedown/Corrections process** (`docs/CONTENT_TAKEDOWN_POLICY.md`)
   - where to report rights/content issues
   - response target (e.g., ack in 3 business days)

## P1 (strongly recommended)

6. **Trademark & Affiliation Notice** (`docs/TRADEMARK_NOTICE.md`)
   - explicitly state non-affiliation unless authorized

7. **Content Provenance Manifest** (`docs/CONTENT_MANIFEST.md`)
   - source URL, retrieval date, ZIM filename/hash, license, attribution string

8. **Release compliance checklist gate** (CI/manual)
   - fail release if required notices are missing

## P2 (nice-to-have for maturity)

9. Incident response playbook for harmful-content reports  
10. Versioned legal docs changelog

---

## 5) Copy-Paste Templates

## A) README disclaimer template (short form)

```md
## Important Safety & License Notice

This project redistributes third-party offline knowledge content (including medical, infrastructure, and technical materials). Content is provided for informational/educational purposes only and may be incomplete, outdated, or inaccurate.

- **Not medical or professional advice.**
- In emergencies, contact local emergency services / qualified professionals.
- Verify critical procedures (first aid, water treatment, shelter/structural guidance) with current local authorities and standards.

Third-party content remains subject to its original licenses and attribution requirements. See:
- `docs/THIRD_PARTY_CONTENT_NOTICE.md`
- `docs/SAFETY_AND_MEDICAL_DISCLAIMER.md`
- `docs/TRADEMARK_NOTICE.md`
```

## B) In-app first-run modal template

```text
Safety Notice
This offline kit includes user-generated and third-party reference content. It may be incomplete, outdated, or incorrect.

Not medical/professional advice. For emergencies, contact local emergency services immediately.

Before acting on first-aid, water-treatment, or shelter guidance, verify against current local authorities, official manuals, and qualified professionals.

By continuing, you acknowledge you are using this content at your own risk.
[Accept] [View Full Notices]
```

## C) In-app footer notice template (compact)

```text
Informational use only — not medical/professional advice. Verify critical safety steps with local official guidance.
```

## D) Takedown policy template (short)

```md
# Content Takedown / Correction Requests

If you believe content in this distribution infringes rights, lacks required attribution, or presents dangerous inaccuracies, contact: <maintainer-email>

Please include:
- Exact file/content reference
- Basis for request (license/rights/safety/correction)
- Supporting links or documentation

Process targets:
- Acknowledge receipt within 3 business days
- Initial decision/update within 10 business days
```

---

## 6) Verification Steps Before Publishing Any Public Artifact

1. Build a manifest for each `.zim` with source + license + attribution text + hash.  
2. Confirm README includes the short disclaimer block.  
3. Confirm UI shows first-run safety notice and link to full notices.  
4. Confirm OpenStreetMap attribution is visible wherever map/data is displayed.  
5. Confirm contact channel exists for takedown/corrections.  
6. Keep a release snapshot (manifest + notices) in version control.

---

## 7) Source Notes (for implementation context)

- Wikipedia copyright/reuse notes: `https://en.wikipedia.org/wiki/Wikipedia:Copyrights`
- OpenStreetMap copyright & license summary: `https://www.openstreetmap.org/copyright`
- Kiwix terms (content responsibility / no warranty framing): `https://get.kiwix.org/en/terms-conditions/`
- Creative Commons BY-SA 4.0 deed summary: `https://creativecommons.org/licenses/by-sa/4.0/`
- Stack Overflow attribution expectations (historical but useful implementation guidance): `https://stackoverflow.blog/2009/06/25/attribution-required/`

> Again: validate these against current official terms at release time.

---

## 8) Priority Recommendations

## Priority 1 (do now)
- Add the four P0 docs + README disclaimer block
- Add first-run in-app notice + footer safety hint

## Priority 2 (this week)
- Create `CONTENT_MANIFEST.md` with per-ZIM metadata, license, attribution
- Add release checklist gate for compliance artifacts

## Priority 3 (before broader distribution)
- Counsel review of redistribution model, especially around bundled copies of large third-party datasets
- Establish recurring review process for license/version changes
