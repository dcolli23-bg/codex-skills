# Template-preserving PPTX authoring

Use `zipfile` and standard-library XML tools. Keep the source archive immutable;
write a distinct revision file. The template is the design source, not merely a
logo source. Inspect its slide text/shapes, relationships, placeholder indices,
layout, size, and inherited font/geometry before building.

## Inspect and edit

Run the bundled validator on the unmodified template first to inventory slide
text and package structure:

```bash
python3 ~/.codex/skills/sprint-retro-powerpoint/scripts/validate_pptx.py \
  /absolute/work/source/template.pptx
```

For deeper inspection, read these ZIP parts:

| Parts | Purpose |
| --- | --- |
| `ppt/presentation.xml` and its `.rels` | Slide order, size, and slide relationship IDs |
| `ppt/slides/slide*.xml` and their `.rels` | Editable shapes/text, layout and notes links |
| `ppt/slideLayouts/`, `ppt/slideMasters/` | Inherited placeholder geometry, fonts, and design |
| `ppt/notesSlides/`, `ppt/notesMasters/` | Speaker notes and notes design |
| `[Content_Types].xml`, `docProps/` | Package inventory and document metadata |

Author an isolated local build script whose content comes from the selected
sprint snapshots. Do not hardcode another sprint's titles, counts, cutoffs, or
shape IDs. Reuse compatible template slides/shapes instead of recreating artwork.
Replace text in the relevant `a:t` runs, preserving text styles; if rebuilding
paragraphs, retain or explicitly reproduce their paragraph/run properties.
Use `a:br` for line breaks, and `xml:space="preserve"` when whitespace requires it.
Prefer shortening copy to shrinking it below the template's readable text size.

For more slides, clone the appropriate template slide and its relationships.
Give each new slide a unique presentation slide ID, relationship IDs unique
within each owning part, and fresh creation IDs where present. Update slide
ordering, notes links/backlinks, content types, and affected document properties
consistently. Do not copy a notes link that points several slides to one notes
page. Preserve existing speaker notes when updating a user-edited deck.

Keep original masters, layouts, themes, media, embedded fonts, and notes masters
byte-identical. Copy untouched ZIP entries as raw bytes; serialize **only** parts
that need changes. Do not delete design parts just because they appear unused.
Retain slide dimensions and inherited geometry. Do not substitute fonts.

## Serialization conventions that matter to Box

Well-formed XML is not sufficient for this renderer. During the successful
Sprint 24 trial, Box rejected packages with prefixed OPC container roots, while
the same content succeeded with their original default namespaces:

```xml
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <!-- Default / Override entries -->
</Types>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <!-- Relationship entries -->
</Relationships>
```

Preserve this convention in **every** modified `.rels` and
`[Content_Types].xml`, including added parts. Do not emit `<ns0:Relationships>`
or `<ns0:Types>`. These are observed Box compatibility constraints, not a claim
that prefixed roots violate the XML namespace standard.

`xml.etree.ElementTree` can discard namespace declarations used only in attribute
values. Preserve in-scope bindings referenced by `mc:Ignorable`,
`mc:MustUnderstand`, `mc:ProcessContent`, `mc:PreserveElements`,
`mc:PreserveAttributes`, `Requires`, and QName values such as `xsi:type`.
`xml.dom.minidom` is a standard-library option for editing existing DOMs while
retaining declarations; inspect its output too. If using ElementTree, collect and
restore necessary declarations and register the correct default namespace before
serializing each OPC container. Do not solve namespace loss by stripping
compatibility attributes or unknown extension data.

Preserve valid XML declarations, encoding, escaped text, all relationship
targets, and ZIP package integrity. Never apply a global regex/string replacement
across the archive. A narrowly verified substitution in a known XML text node is
different from an unbounded package rewrite.

## Structural and content QA

The bundled validator checks CRCs, duplicate ZIP entries, XML parsing, compatibility
prefix bindings, OPC default namespaces, content-type coverage, relationship
targets/references, slide order/IDs, speaker-note links, dimensions, and protected
template parts. Its JSON includes slide and note text for a content review.
It does **not** validate every OOXML schema rule, measure text overflow, prove
render fidelity, or replace image inspection.

Also verify narrative and source fidelity: no template instructional placeholders,
no stale pending/merged statuses, no dropped caveats, and no accidental team
commitments. Preserve source pointers and full metric definitions in notes.
For fresh decks, every slide should have useful speaker notes, not only a page
number. For explicit updates, inspect differences from the downloaded deck and
preserve unrelated authored content.

Use the final Box-rendered PDF/PNGs for acceptance. A local diagnostic renderer
may help diagnose a package, but must not rewrite the final PPTX or substitute
for Box QA.
