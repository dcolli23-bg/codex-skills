"""Replace only the generated session-log section; preserve the surrounding note."""
import re
from common import atomic_write

HEADING = '## Codex Session Logs'
START = '<!-- codex-session-logs:start -->'
END = '<!-- codex-session-logs:end -->'


def replace_section(original, body):
    newline = '\r\n' if '\r\n' in original else '\n'
    text = original.replace('\r\n', '\n')
    section = f'{HEADING}\n\n{START}\n{body.rstrip()}\n{END}\n'
    if START in text or END in text:
        if text.count(START) != 1 or text.count(END) != 1:
            raise ValueError('Ambiguous generated-section markers; leaving note unchanged')
        start, end = text.index(START), text.index(END) + len(END)
        if end < start:
            raise ValueError('Reversed generated-section markers')
        result = text[:start] + START + '\n' + body.rstrip() + '\n' + END + text[end:]
    else:
        # Parse only actual Markdown headings, ignoring fenced code and YAML frontmatter.
        headings = []
        offset = 0
        fence = None
        frontmatter = text.startswith('---\n')
        for number, line in enumerate(text.splitlines(keepends=True)):
            if frontmatter:
                if number > 0 and line.strip() in ('---', '...'):
                    frontmatter = False
            elif re.match(r'^\s{0,3}(`{3,}|~{3,})', line):
                token = line.lstrip()[0]
                fence = None if fence == token else token if fence is None else fence
            elif fence is None:
                m = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
                if m:
                    headings.append((offset, len(m[1]), m[2]))
            offset += len(line)
        matches = [h for h in headings if h[1:] == (2, 'Codex Session Logs')]
        if len(matches) > 1:
            raise ValueError('Multiple Codex Session Logs sections; leaving note unchanged')
        if matches:
            start = matches[0][0]
            end = next((h[0] for h in headings if h[0] > start and h[1] <= 2), len(text))
            result = text[:start] + section + '\n' + text[end:]
        else:
            parent = next((h for h in headings if h[1:] == (1, "Where I'm Leaving Off")), None)
            if parent:
                end = next((h[0] for h in headings if h[0] > parent[0] and h[1] == 1), len(text))
                result = text[:end].rstrip('\n') + '\n\n' + section + '\n' + text[end:]
            else:
                result = text.rstrip('\n') + "\n\n# Where I'm Leaving Off\n\n" + section
    return result.replace('\n', newline)


def write_note(path, body):
    """Read just before writing; detect concurrent edits rather than overwrite them."""
    if not path.exists():
        return False
    before = path.read_bytes()
    after = replace_section(before.decode(), body).encode()
    if before == after:
        return True
    if path.read_bytes() != before:
        raise RuntimeError('Daily note changed during update; retry on next run')
    atomic_write(path, after.decode())
    return True
