#!/usr/bin/env python3
"""Offline PPTX/package checks; visual acceptance still requires Box renders."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import posixpath
import sys
from urllib.parse import unquote, urlsplit
from xml.dom import minidom
from xml.parsers.expat import ExpatError
import xml.etree.ElementTree as ET
import zipfile


P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
N = {"p": P, "a": A}
PROTECTED = (
    "ppt/slideMasters/", "ppt/slideLayouts/", "ppt/theme/", "ppt/media/",
    "ppt/notesMasters/", "ppt/fonts/", "ppt/embeddings/",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def xml_root(data, name):
    """Parse and check lexical prefix references that ordinary parsing misses."""
    scopes, pending, root = [], {}, None
    for event, item in ET.iterparse(
        io.BytesIO(data), events=("start-ns", "start", "end")
    ):
        if event == "start-ns":
            pending[item[0]] = item[1]
        elif event == "start":
            scope = dict(scopes[-1]) if scopes else {
                "xml": "http://www.w3.org/XML/1998/namespace"
            }
            scope.update(pending)
            pending.clear()
            if root is None:
                root = item
                expected = PKG if name.endswith(".rels") else (
                    CT if name == "[Content_Types].xml" else None
                )
                if expected:
                    local = "Relationships" if expected == PKG else "Types"
                    require(item.tag == f"{{{expected}}}{local}",
                            f"{name}: wrong OPC root")
                    require(scope.get("") == expected,
                            f"{name}: OPC root needs its default namespace for Box")
                    with minidom.parseString(data) as document:
                        require(document.documentElement.prefix is None,
                                f"{name}: prefixed OPC root is incompatible with Box")
            scopes.append(scope)
            for attr, value in item.attrib.items():
                if attr in (f"{{{MC}}}Ignorable", f"{{{MC}}}MustUnderstand",
                            "Requires"):
                    prefixes = value.split()
                elif attr in (f"{{{MC}}}ProcessContent", f"{{{MC}}}PreserveElements",
                              f"{{{MC}}}PreserveAttributes", f"{{{XSI}}}type"):
                    prefixes = [q.split(":", 1)[0] for q in value.split() if ":" in q]
                else:
                    continue
                for prefix in prefixes:
                    require(prefix in scope,
                            f"{name}: undeclared value prefix {prefix!r}")
        else:
            scopes.pop()
    return root


def rel_owner(name):
    if name == "_rels/.rels":
        return ""
    folder, leaf = posixpath.split(name)
    require(posixpath.basename(folder) == "_rels",
            f"{name}: relationships part outside _rels")
    return posixpath.join(posixpath.dirname(folder), leaf.removesuffix(".rels"))


def resolve_target(owner, target):
    uri = urlsplit(target)
    require(not uri.scheme and not uri.netloc,
            f"{owner}: external URI without TargetMode=External")
    path = unquote(uri.path)
    if not path:
        return owner
    if path.startswith("/"):
        return posixpath.normpath(path).lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(owner), path))


def load_package(path):
    with zipfile.ZipFile(path) as archive:
        names = [info.filename for info in archive.infolist()]
        require(len(names) == len(set(names)), "Duplicate ZIP entry")
        for name in names:
            require(not name.startswith("/") and "\\" not in name
                    and ".." not in name.split("/"), f"Unsafe ZIP name: {name}")
        require(archive.testzip() is None, "ZIP CRC failure")
        parts = {name: archive.read(name) for name in names if not name.endswith("/")}
    roots = {name: xml_root(data, name) for name, data in parts.items()
             if name.endswith((".xml", ".rels"))}
    for required in ("[Content_Types].xml", "ppt/presentation.xml",
                     "ppt/_rels/presentation.xml.rels", "_rels/.rels"):
        require(required in roots, f"Missing required part: {required}")
    rels = {}
    for name, root in roots.items():
        if not name.endswith(".rels"):
            continue
        owner = rel_owner(name)
        require(not owner or owner in parts, f"{name}: missing owning part {owner}")
        rels[owner] = {}
        for rel in root:
            rid, target, kind = rel.get("Id"), rel.get("Target"), rel.get("Type")
            require(rel.tag == f"{{{PKG}}}Relationship" and rid and target and kind,
                    f"{name}: incomplete relationship")
            require(rid not in rels[owner], f"{name}: duplicate relationship ID {rid}")
            resolved = None
            if rel.get("TargetMode") != "External":
                resolved = resolve_target(owner, target)
                require(resolved in parts, f"{name}: missing target {resolved}")
            rels[owner][rid] = (kind, resolved)
    documents = [target for kind, target in rels.get("", {}).values()
                 if kind == R + "/officeDocument"]
    require(documents == ["ppt/presentation.xml"], "Wrong root officeDocument link")
    for name, root in roots.items():
        if name.endswith(".rels"):
            continue
        for element in root.iter():
            for attr, rid in element.attrib.items():
                if attr in (f"{{{R}}}id", f"{{{R}}}embed", f"{{{R}}}link"):
                    require(rid in rels.get(name, {}),
                            f"{name}: undefined relationship reference {rid}")
    defaults, overrides = {}, {}
    for entry in roots["[Content_Types].xml"]:
        if entry.tag == f"{{{CT}}}Default":
            key, dest = entry.get("Extension"), defaults
        else:
            require(entry.tag == f"{{{CT}}}Override", "Unknown content-type element")
            key, dest = entry.get("PartName"), overrides
            require(key and key.startswith("/") and key[1:] in parts,
                    f"Content-type override has no part: {key}")
        require(key and key not in dest and entry.get("ContentType"),
                f"Missing/duplicate content-type entry: {key}")
        dest[key] = entry.get("ContentType")
    for name in parts:
        if name != "[Content_Types].xml":
            require("/" + name in overrides or name.rsplit(".", 1)[-1] in defaults,
                    f"No content type for {name}")
    return parts, roots, rels


def text_of(root):
    return [node.text or "" for node in root.findall(".//a:t", N)]


def validate(path, template=None, expected_slides=None, require_notes=False):
    parts, roots, rels = load_package(path)
    pres = roots["ppt/presentation.xml"]
    require(pres.tag == f"{{{P}}}presentation", "Wrong presentation root")
    size = pres.find("p:sldSz", N)
    require(size is not None and size.get("cx") and size.get("cy"),
            "Missing slide dimensions")
    inventory = pres.find("p:sldIdLst", N)
    ids = list(inventory) if inventory is not None else []
    require(ids, "Presentation has no slides")
    if expected_slides is not None:
        require(len(ids) == expected_slides,
                f"Expected {expected_slides} slides, found {len(ids)}")
    slide_ids = [slide.get("id") for slide in ids]
    require(all(slide_ids) and len(set(slide_ids)) == len(ids),
            "Missing/duplicate presentation slide ID")
    slide_parts, notes_parts, slides = set(), set(), []
    for index, entry in enumerate(ids, 1):
        rid = entry.get(f"{{{R}}}id")
        kind, name = rels["ppt/presentation.xml"].get(rid, ("", None))
        require(kind == R + "/slide" and name in roots,
                f"Slide {index}: missing/internal slide relationship")
        require(name not in slide_parts, f"Repeated slide part: {name}")
        slide_parts.add(name)
        root = roots[name]
        require(root.tag == f"{{{P}}}sld", f"{name}: wrong slide root")
        layouts = [target for kind, target in rels.get(name, {}).values()
                   if kind == R + "/slideLayout"]
        require(len(layouts) == 1 and layouts[0] in roots
                and roots[layouts[0]].tag == f"{{{P}}}sldLayout",
                f"{name}: missing/invalid slide layout")
        shape_ids = [node.get("id") for node in root.findall(".//p:cNvPr", N)]
        require(all(shape_ids) and len(shape_ids) == len(set(shape_ids)),
                f"{name}: missing/duplicate shape ID")
        notes = [target for kind, target in rels.get(name, {}).values()
                 if kind == R + "/notesSlide"]
        require(len(notes) <= 1, f"{name}: multiple notes links")
        if require_notes:
            require(notes, f"{name}: missing speaker notes")
        note_text = []
        if notes:
            note = notes[0]
            require(note in roots and roots[note].tag == f"{{{P}}}notes",
                    f"{name}: invalid notes part")
            require(note not in notes_parts, f"{name}: shared notes page")
            notes_parts.add(note)
            backlinks = [target for kind, target in rels.get(note, {}).values()
                         if kind == R + "/slide"]
            require(backlinks == [name], f"{note}: incorrect slide backlink")
            masters = [target for kind, target in rels.get(note, {}).values()
                       if kind == R + "/notesMaster"]
            require(len(masters) == 1 and masters[0] in roots
                    and roots[masters[0]].tag == f"{{{P}}}notesMaster",
                    f"{note}: missing/invalid notes master")
            note_text = text_of(roots[note])
            bodies = [shape for shape in roots[note].findall(".//p:sp", N)
                      if shape.find(".//p:ph[@type='body']", N) is not None]
            if require_notes:
                require(any("".join(text_of(body)).strip() for body in bodies),
                        f"{note}: empty speaker-note body")
        slides.append({"slide": index, "part": name, "text": text_of(root),
                       "notes_part": notes[0] if notes else None,
                       "notes_text": note_text})
    preserved, modified, added = [], [], []
    if template is not None:
        source, source_roots, _ = load_package(template)
        source_size = source_roots["ppt/presentation.xml"].find("p:sldSz", N)
        require(source_size is not None and source_size.attrib == size.attrib,
                "Slide dimensions differ from template")
        for name, data in source.items():
            if name.startswith(PROTECTED):
                require(parts.get(name) == data, f"Protected template part changed: {name}")
                preserved.append(name)
        modified = sorted(name for name in source if parts.get(name) != source[name])
        added = sorted(set(parts) - set(source))
    raw = Path(path).read_bytes()
    return {
        "status": "pass", "scope": "Structural checks only; not visual acceptance",
        "path": str(Path(path).resolve()), "sha1": hashlib.sha1(raw).hexdigest(),
        "sha256": hashlib.sha256(raw).hexdigest(), "slide_count": len(ids),
        "slide_dimensions": size.attrib, "slides": slides,
        "protected_parts_preserved": len(preserved),
        "modified_or_removed_parts": modified, "added_parts": added,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--expected-slides", type=int)
    parser.add_argument("--require-notes", action="store_true")
    args = parser.parse_args()
    try:
        report = validate(args.pptx, args.template, args.expected_slides, args.require_notes)
    except (ValueError, OSError, zipfile.BadZipFile, ET.ParseError, ExpatError) as error:
        print(json.dumps({"status": "fail", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
