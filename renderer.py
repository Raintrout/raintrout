from math import ceil
from typing import Iterable

from sections import Line, Section, WorkBlock, WorkEntry

LOW_CONTEXT_TRAILING_WORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from",
    "in", "of", "on", "or", "the", "to", "with",
}

WORK_MARKER_DX = 8
WORK_TEXT_DX = 20
WORK_MARKER_Y_OFFSET = 6
WORK_MARKER_RADIUS = 4


def tspan(
    content: str = "",
    *,
    x: int | None = None,
    y: int | None = None,
    cls: str | None = None,
    preserve_space: bool = False,
) -> str:
    attrs = []
    if x is not None:
        attrs.append(f'x="{x}"')
    if y is not None:
        attrs.append(f'y="{y}"')
    if cls is not None:
        attrs.append(f'class="{cls}"')
    if preserve_space:
        attrs.append('xml:space="preserve"')
    prefix = "<tspan" + ((" " + " ".join(attrs)) if attrs else "")
    return f"{prefix}>{content}</tspan>"


def render_key(keys: list[str]) -> str:
    return '.'.join(tspan(key, cls="key") for key in keys)


def should_shift_boundary(previous_line: str, next_line: str) -> bool:
    previous_words = previous_line.split()
    next_words = next_line.split()
    if not previous_words or len(next_words) < 2:
        return False

    trailing_word = previous_words[-1].lower().strip(",.;:!?")
    return trailing_word in LOW_CONTEXT_TRAILING_WORDS


def split_value(value: str, line_length: int) -> list[str]:
    expected_lines = max(1, ceil(len(value) / line_length))
    words = value.split()

    if expected_lines == 1 or len(words) <= 1:
        return [value]

    lines = []
    current_words = []
    current_length = 0
    remaining_text_length = len(value)
    remaining_lines = expected_lines

    for word in words:
        separator_length = 1 if current_words else 0
        proposed_length = current_length + separator_length + len(word)
        target_length = remaining_text_length / remaining_lines

        if current_words and proposed_length > target_length:
            lines.append(' '.join(current_words))
            remaining_text_length -= current_length + 1
            remaining_lines -= 1
            current_words = [word]
            current_length = len(word)
            continue

        current_words.append(word)
        current_length = proposed_length

    if current_words:
        lines.append(' '.join(current_words))

    for index in range(len(lines) - 1):
        while should_shift_boundary(lines[index], lines[index + 1]):
            next_words = lines[index + 1].split()
            lines[index] = f"{lines[index]} {next_words[0]}"
            lines[index + 1] = ' '.join(next_words[1:])

    return lines


def _section_header_line(header: str, *, x: int, y: int, line_length: int, is_first: bool) -> str:
    label = header if is_first else f"- {header}"
    padding = line_length - 1 - len(label)
    return tspan(label, x=x, y=y) + " " + "—" * padding


def _regular_line(item: Line, *, x: int, y: int, line_length: int) -> Iterable[str]:
    key = '.'.join(item.key)
    value = item.value
    rendered_key = render_key(item.key)

    if len(value) + len(key) <= line_length - 10:
        dots = "." * (line_length - 5 - len(key) - len(value))
        yield (
            tspan(". ", x=x, y=y, cls="cc")
            + f"{rendered_key}:"
            + tspan(f" {dots} ", cls="cc")
            + tspan(value, cls="value")
        )
        return

    for value_index, part in enumerate(split_value(value, line_length - 5 - len(key))):
        if value_index == 0:
            dots = "." * (line_length - 5 - len(key) - len(part))
            yield (
                tspan(". ", x=x, y=y, cls="cc")
                + f"{rendered_key}:"
                + tspan(f" {dots} ", cls="cc")
                + tspan(part, cls="value")
            )
        else:
            dots = "." * (line_length - 5 - len(part))
            yield (
                tspan(". ", x=x, y=y, cls="cc")
                + tspan(f" {dots} ", cls="cc")
                + tspan(part, cls="value")
            )


def _work_entry_line(entry: WorkEntry, value: str, *, text_x: int, y: int, line_length: int) -> str:
    key = '.'.join(entry.key)
    dots = "." * max(1, line_length - 4 - len(key) - len(value))
    return (
        tspan(render_key(entry.key), x=text_x, y=y)
        + tspan(f" {dots} ", cls="cc")
        + tspan(value, cls="value")
    )


def _work_wrap_continuation(entry: WorkEntry, value: str, *, text_x: int, y: int, line_length: int) -> str:
    key = '.'.join(entry.key)
    gap = " " * max(1, line_length - 4 - len(key) - len(value))
    return (
        tspan(render_key(entry.key), x=text_x, y=y)
        + tspan(f" {gap} ", cls="cc", preserve_space=True)
        + tspan(value, cls="value")
    )


def _work_gap_continuation(value: str, *, text_x: int, y: int, line_length: int) -> str:
    gap = " " * max(1, line_length - 4 - len(value))
    return (
        tspan(f" {gap} ", x=text_x, y=y, cls="cc", preserve_space=True)
        + tspan(value, cls="value")
    )


def _work_key_only_line(entry: WorkEntry, *, text_x: int, y: int) -> str:
    return tspan(render_key(entry.key), x=text_x, y=y)


def _render_work_block(
    block: WorkBlock,
    *,
    text_x: int,
    y: int,
    line_height: int,
    line_length: int,
) -> tuple[list[str], list[WorkEntry], int]:
    primary = block.primary
    followers = block.followers
    primary_key_len = len(".".join(primary.key))
    value = primary.summary

    svg_lines: list[str] = []
    entries: list[WorkEntry] = [primary]

    wraps = len(value) + primary_key_len > line_length - 10

    if not wraps:
        svg_lines.append(_work_entry_line(primary, value, text_x=text_x, y=y, line_length=line_length))
        y += line_height
        standalone_followers = followers
    else:
        parts = split_value(value, line_length - 4 - primary_key_len)
        attached_follower = followers[0] if followers else None
        for value_index, part in enumerate(parts):
            if value_index == 0:
                svg_lines.append(_work_entry_line(primary, part, text_x=text_x, y=y, line_length=line_length))
            elif value_index == 1 and attached_follower is not None:
                entries.append(attached_follower)
                svg_lines.append(_work_wrap_continuation(
                    attached_follower, part, text_x=text_x, y=y, line_length=line_length,
                ))
            else:
                svg_lines.append(_work_gap_continuation(part, text_x=text_x, y=y, line_length=line_length))
            y += line_height
        # Followers list is always advanced by one when wrapping (matching prior peek-ahead
        # semantics, even when split produced only one part).
        standalone_followers = followers[1:] if followers else []

    for follower in standalone_followers:
        entries.append(follower)
        svg_lines.append(_work_key_only_line(follower, text_x=text_x, y=y))
        y += line_height

    return svg_lines, entries, y


def render(
    sections: Iterable[Section],
    offset_x: int = 390,
    offset_y: int = 30,
    line_length: int = 60,
    line_height: int = 20,
    max_y: int = 510,
    work_timeline_line_color: str = "#616e7f",
) -> tuple[list[str], list[str]]:
    lines: list[str] = []
    overlays: list[str] = []

    for section_index, section in enumerate(sections):
        lines.append(_section_header_line(
            section.header, x=offset_x, y=offset_y,
            line_length=line_length, is_first=(section_index == 0),
        ))
        offset_y += line_height

        work_marker_x = offset_x + WORK_MARKER_DX
        work_text_x = offset_x + WORK_TEXT_DX
        work_entries: list[WorkEntry] = []
        work_line_start_y: int | None = None
        work_line_end_y: int | None = None

        for item in section.lines:
            if isinstance(item, WorkBlock):
                if work_line_start_y is None:
                    work_line_start_y = offset_y - WORK_MARKER_Y_OFFSET
                block_lines, block_entries, offset_y = _render_work_block(
                    item, text_x=work_text_x, y=offset_y,
                    line_height=line_height, line_length=line_length,
                )
                lines.extend(block_lines)
                work_entries.extend(block_entries)
                work_line_end_y = offset_y - WORK_MARKER_Y_OFFSET
            else:
                for svg in _regular_line(item, x=offset_x, y=offset_y, line_length=line_length):
                    lines.append(svg)
                    offset_y += line_height

        lines.append(tspan(x=offset_x, y=offset_y))
        offset_y += line_height

        if section.header == "Work" and work_entries:
            assert work_line_start_y is not None and work_line_end_y is not None
            overlays.extend(
                _work_timeline_overlays(
                    work_entries,
                    work_marker_x=work_marker_x,
                    line_start_y=work_line_start_y,
                    line_end_y=work_line_end_y,
                    line_color=work_timeline_line_color,
                )
            )

    while offset_y <= max_y:
        lines.append(tspan(". ", x=offset_x, y=offset_y, cls="cc"))
        offset_y += line_height

    return lines, overlays


def _work_timeline_overlays(
    entries: list[WorkEntry],
    *,
    work_marker_x: int,
    line_start_y: int,
    line_end_y: int,
    line_color: str,
) -> Iterable[str]:
    yield (
        f'<line x1="{work_marker_x}" y1="{line_start_y}" '
        f'x2="{work_marker_x}" y2="{line_end_y}" '
        f'stroke="{line_color}" stroke-width="2"/>'
    )

    newest_start = entries[0].start
    oldest_start = entries[-1].start
    total_months = max(
        1,
        (newest_start.year - oldest_start.year) * 12
        + (newest_start.month - oldest_start.month),
    )
    vertical_span = max(1, line_end_y - line_start_y)
    for entry in entries:
        months_from_latest = (
            (newest_start.year - entry.start.year) * 12
            + (newest_start.month - entry.start.month)
        )
        event_y = line_start_y + round((months_from_latest / total_months) * vertical_span)
        yield (
            f'<circle cx="{work_marker_x}" cy="{event_y}" '
            f'r="{WORK_MARKER_RADIUS}" class="{entry.marker_class}"/>'
        )
