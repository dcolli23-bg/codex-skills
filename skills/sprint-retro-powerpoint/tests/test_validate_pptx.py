"""Minimal synthetic packages test invariants, not complete OOXML schemas."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_pptx.py"
SPEC = importlib.util.spec_from_file_location("validate_pptx", SCRIPT)
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


def relationships(*entries):
    children = "".join(
        f'<Relationship Id="{rid}" Type="{V.R}/{kind}" Target="{target}"{mode}/>'
        for rid, kind, target, mode in entries
    )
    return f'<Relationships xmlns="{V.PKG}">{children}</Relationships>'.encode()


def fixture():
    return {
        "[Content_Types].xml": (
            f'<Types xmlns="{V.CT}">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="png" ContentType="image/png"/></Types>'
        ).encode(),
        "_rels/.rels": relationships(
            ("rId1", "officeDocument", "/ppt/presentation.xml", "")),
        "ppt/presentation.xml": (
            f'<p:presentation xmlns:p="{V.P}" xmlns:r="{V.R}">'
            '<p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst>'
            '<p:sldSz cx="12192000" cy="6858000"/></p:presentation>'
        ).encode(),
        "ppt/_rels/presentation.xml.rels": relationships(
            ("rId1", "slide", "slides/slide1.xml", "")),
        "ppt/slides/slide1.xml": (
            f'<p:sld xmlns:p="{V.P}" xmlns:a="{V.A}">'
            '<p:cSld><p:spTree><p:sp><p:cNvPr id="1"/>'
            '<p:txBody><a:p><a:r><a:t>Editable title</a:t></a:r></a:p>'
            '</p:txBody></p:sp></p:spTree></p:cSld></p:sld>'
        ).encode(),
        "ppt/slides/_rels/slide1.xml.rels": relationships(
            ("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml", ""),
            ("rId2", "notesSlide", "../notesSlides/notesSlide1.xml", "")),
        "ppt/slideLayouts/slideLayout1.xml": (
            f'<p:sldLayout xmlns:p="{V.P}"/>').encode(),
        "ppt/notesSlides/notesSlide1.xml": (
            f'<p:notes xmlns:p="{V.P}" xmlns:a="{V.A}"><p:cSld><p:spTree>'
            '<p:sp><p:nvSpPr><p:nvPr><p:ph type="body"/></p:nvPr></p:nvSpPr>'
            '<p:txBody><a:p><a:r><a:t>Evidence and caveats</a:t></a:r></a:p>'
            '</p:txBody></p:sp></p:spTree></p:cSld></p:notes>'
        ).encode(),
        "ppt/notesSlides/_rels/notesSlide1.xml.rels": relationships(
            ("rId1", "slide", "../slides/slide1.xml", ""),
            ("rId2", "notesMaster", "../notesMasters/notesMaster1.xml", "")),
        "ppt/notesMasters/notesMaster1.xml": (
            f'<p:notesMaster xmlns:p="{V.P}"/>').encode(),
        "ppt/media/bg.png": b"synthetic-image-bytes",
    }


class PackageChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.parts = fixture()
        self.source = self.write("template.pptx", self.parts)

    def write(self, name, parts):
        path = self.folder / name
        with zipfile.ZipFile(path, "w") as archive:
            for part, data in parts.items():
                archive.writestr(part, data)
        return path

    def check(self, parts=None, **kwargs):
        candidate = self.write("candidate.pptx", self.parts if parts is None else parts)
        return V.validate(candidate, template=self.source, **kwargs)

    def test_valid_package_has_editable_slide_and_notes_inventory(self):
        report = self.check(expected_slides=1, require_notes=True)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["slides"][0]["text"], ["Editable title"])
        self.assertEqual(report["slides"][0]["notes_text"], ["Evidence and caveats"])
        self.assertEqual(report["protected_parts_preserved"], 3)
        self.assertEqual(report["modified_or_removed_parts"], [])

    def test_changed_text_is_allowed(self):
        self.parts["ppt/slides/slide1.xml"] = self.parts["ppt/slides/slide1.xml"].replace(
            b"Editable title", b"Current sprint &amp; status")
        report = self.check(require_notes=True)
        self.assertEqual(report["slides"][0]["text"], ["Current sprint & status"])
        self.assertEqual(report["modified_or_removed_parts"], ["ppt/slides/slide1.xml"])

    def test_default_namespaces_required_for_opc_containers(self):
        for name in ("[Content_Types].xml", "ppt/slides/_rels/slide1.xml.rels"):
            with self.subTest(name=name):
                parts = dict(self.parts)
                data = parts[name].replace(b"xmlns=", b"xmlns:ns0=")
                root = b"Types" if name.startswith("[") else b"Relationships"
                children = (b"Default",) if root == b"Types" else (b"Relationship",)
                for tag in (root, *children):
                    data = data.replace(b"<" + tag, b"<ns0:" + tag)
                    data = data.replace(b"</" + tag, b"</ns0:" + tag)
                parts[name] = data
                with self.assertRaisesRegex(ValueError, "default namespace"):
                    self.check(parts)

    def test_prefixed_root_rejected_even_with_default_binding(self):
        name = "ppt/slides/_rels/slide1.xml.rels"
        self.parts[name] = self.parts[name].replace(
            b"<Relationships ", f'<q:Relationships xmlns:q="{V.PKG}" '.encode()
        ).replace(b"</Relationships>", b"</q:Relationships>")
        with self.assertRaisesRegex(ValueError, "prefixed OPC root"):
            self.check()

    def test_compatibility_prefix_bindings_are_in_scope(self):
        name = "ppt/slides/slide1.xml"
        for attr in ('mc:Ignorable="ext"', 'mc:MustUnderstand="ext"',
                     'mc:ProcessContent="ext:element"', 'mc:PreserveAttributes="ext:*"',
                     'mc:PreserveElements="ext:element"', 'Requires="ext"'):
            with self.subTest(attr=attr):
                parts = dict(self.parts)
                parts[name] = parts[name].replace(
                    b"<p:sld ", f'<p:sld xmlns:mc="{V.MC}" {attr} '.encode())
                with self.assertRaisesRegex(ValueError, "undeclared value prefix"):
                    self.check(parts)
                parts[name] = parts[name].replace(
                    b"<p:sld ", b'<p:sld xmlns:ext="urn:synthetic-extension" ')
                self.check(parts)

    def test_qname_type_prefix_is_checked(self):
        name = "ppt/slides/slide1.xml"
        self.parts[name] = self.parts[name].replace(
            b"<p:sld ", f'<p:sld xmlns:xsi="{V.XSI}" xsi:type="lost:Type" '.encode())
        with self.assertRaisesRegex(ValueError, "undeclared value prefix"):
            self.check()

    def test_relationship_targets_and_references_are_checked(self):
        for old, new, message in (
            (b"slides/slide1.xml", b"slides/missing.xml", "missing target"),
            (b'Id="rId1"', b'Id="changed"', "undefined relationship"),
        ):
            with self.subTest(message=message):
                parts = dict(self.parts)
                name = "ppt/_rels/presentation.xml.rels"
                parts[name] = parts[name].replace(old, new)
                with self.assertRaisesRegex(ValueError, message):
                    self.check(parts)

    def test_duplicate_relationship_ids_fail(self):
        name = "ppt/slides/_rels/slide1.xml.rels"
        self.parts[name] = self.parts[name].replace(b'Id="rId2"', b'Id="rId1"')
        with self.assertRaisesRegex(ValueError, "duplicate relationship ID"):
            self.check()

    def test_external_and_percent_encoded_relationships(self):
        self.parts["ppt/media/image with space.png"] = b"image"
        name = "ppt/slides/_rels/slide1.xml.rels"
        self.parts[name] = self.parts[name].replace(b"</Relationships>", (
            f'<Relationship Id="rId3" Type="{V.R}/hyperlink" '
            'Target="https://example.test" TargetMode="External"/>'
            f'<Relationship Id="rId4" Type="{V.R}/image" '
            'Target="../media/image%20with%20space.png"/></Relationships>'
        ).encode())
        self.check()

    def test_missing_content_type_fails(self):
        self.parts["ppt/unknown.bin"] = b"data"
        with self.assertRaisesRegex(ValueError, "No content type"):
            self.check()

    def test_duplicate_content_type_fails(self):
        name = "[Content_Types].xml"
        self.parts[name] = self.parts[name].replace(
            b"</Types>", b'<Default Extension="xml" ContentType="application/xml"/></Types>')
        with self.assertRaisesRegex(ValueError, "duplicate content-type"):
            self.check()

    def test_missing_or_modified_protected_assets_fail(self):
        for remove in (False, True):
            with self.subTest(remove=remove):
                parts = dict(self.parts)
                if remove:
                    del parts["ppt/media/bg.png"]
                else:
                    parts["ppt/media/bg.png"] = b"changed artwork"
                with self.assertRaisesRegex(ValueError, "Protected template part"):
                    self.check(parts)

    def test_slide_count_and_dimensions_checked(self):
        with self.assertRaisesRegex(ValueError, "Expected 3 slides"):
            self.check(expected_slides=3)
        self.parts["ppt/presentation.xml"] = self.parts["ppt/presentation.xml"].replace(
            b'cx="12192000"', b'cx="100"')
        with self.assertRaisesRegex(ValueError, "dimensions differ"):
            self.check()

    def test_shape_ids_unique_within_slide(self):
        name = "ppt/slides/slide1.xml"
        self.parts[name] = self.parts[name].replace(
            b'<p:cNvPr id="1"/>', b'<p:cNvPr id="1"/><p:cNvPr id="1"/>')
        with self.assertRaisesRegex(ValueError, "duplicate shape ID"):
            self.check()

    def test_slide_layout_required(self):
        name = "ppt/slides/_rels/slide1.xml.rels"
        self.parts[name] = relationships(
            ("rId2", "notesSlide", "../notesSlides/notesSlide1.xml", ""))
        with self.assertRaisesRegex(ValueError, "slide layout"):
            self.check()

    def test_speaker_notes_must_have_a_nonempty_body(self):
        name = "ppt/notesSlides/notesSlide1.xml"
        self.parts[name] = self.parts[name].replace(b"Evidence and caveats", b"")
        with self.assertRaisesRegex(ValueError, "empty speaker-note body"):
            self.check(require_notes=True)

    def test_speaker_notes_link_required_when_requested(self):
        name = "ppt/slides/_rels/slide1.xml.rels"
        self.parts[name] = relationships(
            ("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml", ""))
        with self.assertRaisesRegex(ValueError, "missing speaker notes"):
            self.check(require_notes=True)

    def test_notes_backlink_checked(self):
        name = "ppt/notesSlides/_rels/notesSlide1.xml.rels"
        self.parts[name] = self.parts[name].replace(
            (V.R + "/slide").encode(), (V.R + "/not-a-slide").encode())
        with self.assertRaisesRegex(ValueError, "incorrect slide backlink"):
            self.check(require_notes=True)

    def test_duplicate_and_unsafe_zip_entries_fail(self):
        path = self.folder / "unsafe.pptx"
        for name in ("../escape.xml", "ppt/slides/slide1.xml"):
            with self.subTest(name=name):
                self.write(path.name, self.parts)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    with zipfile.ZipFile(path, "a") as archive:
                        archive.writestr(name, b"<extra/>")
                with self.assertRaisesRegex(ValueError, "Unsafe ZIP|Duplicate ZIP"):
                    V.validate(path)

    def test_cli_errors_are_nonzero_and_machine_readable(self):
        invalid = self.folder / "invalid.pptx"
        invalid.write_bytes(b"not a zip")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(invalid)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["status"], "fail")
        self.assertEqual(result.stdout, "")

    def test_cli_malformed_xml_error_is_machine_readable(self):
        self.parts["[Content_Types].xml"] = (
            f'<Types xmlns="{V.CT}"><Broken></Types>').encode()
        invalid = self.write("invalid-xml.pptx", self.parts)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(invalid)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["status"], "fail")
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
