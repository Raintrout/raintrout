from math import ceil
from typing import Iterable

from sections import Line, Section, WorkEntry

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


def _regular_line(item: Line, *, x: int, y: int, line_length: int) -> Iterable[tuple[str, str]]:
    """Yield (svg, _) pairs for a non-work Line, wrapped to line_length."""
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
        work_entry_markers: list[tuple[WorkEntry, int]] = []
        work_line_end_y: int | None = None

        line_index = 0
        while line_index < len(section.lines):
            item = section.lines[line_index]

            if isinstance(item, WorkEntry):
                work_entry_markers.append((item, offset_y - WORK_MARKER_Y_OFFSET))
                key = '.'.join(item.key)
                value = item.summary
                shared_next: WorkEntry | None = None

                if (
                    line_index + 1 < len(section.lines)
                    and isinstance(section.lines[line_index + 1], WorkEntry)
                    and section.lines[line_index + 1].shared_summary
                ):
                    shared_next = section.lines[line_index + 1]

                if item.shared_summary:
                    lines.append(tspan(render_key(item.key), x=work_text_x, y=offset_y))
                    offset_y += line_height
                    line_index += 1
                elif len(value) + len(key) > line_length - 10:
                    for value_index, part in enumerate(split_value(value, line_length - 4 - len(key))):
                        if value_index == 0:
                            dots = "." * max(1, line_length - 4 - len(key) - len(part))
                            lines.append(
                                tspan(render_key(item.key), x=work_text_x, y=offset_y)
                                + tspan(f" {dots} ", cls="cc")
                                + tspan(part, cls="value")
                            )
                        elif value_index == 1 and shared_next is not None:
                            shared_key = ".".join(shared_next.key)
                            work_entry_markers.append((shared_next, offset_y - WORK_MARKER_Y_OFFSET))
                            gap = " " * max(1, line_length - 4 - len(shared_key) - len(part))
                            lines.append(
                                tspan(render_key(shared_next.key), x=work_text_x, y=offset_y)
                                + tspan(f" {gap} ", cls="cc", preserve_space=True)
                                + tspan(part, cls="value")
                            )
                        else:
                            gap = " " * max(1, line_length - 4 - len(part))
                            lines.append(
                                tspan(f" {gap} ", x=work_text_x, y=offset_y, cls="cc", preserve_space=True)
                                + tspan(part, cls="value")
                            )
                        offset_y += line_height
                    line_index += 2 if shared_next is not None else 1
                else:
                    dots = "." * max(1, line_length - 4 - len(key) - len(value))
                    lines.append(
                        tspan(render_key(item.key), x=work_text_x, y=offset_y)
                        + tspan(f" {dots} ", cls="cc")
                        + tspan(value, cls="value")
                    )
                    offset_y += line_height
                    line_index += 1

                work_line_end_y = offset_y - WORK_MARKER_Y_OFFSET
                continue

            for svg in _regular_line(item, x=offset_x, y=offset_y, line_length=line_length):
                lines.append(svg)
                offset_y += line_height
            line_index += 1

        lines.append(tspan(x=offset_x, y=offset_y))
        offset_y += line_height

        if section.header == "Work" and work_entry_markers:
            overlays.extend(
                _work_timeline_overlays(
                    work_entry_markers,
                    work_marker_x=work_marker_x,
                    work_line_end_y=work_line_end_y,
                    line_color=work_timeline_line_color,
                )
            )

    while offset_y <= max_y:
        lines.append(tspan(". ", x=offset_x, y=offset_y, cls="cc"))
        offset_y += line_height

    return lines, overlays


def _work_timeline_overlays(
    markers: list[tuple[WorkEntry, int]],
    *,
    work_marker_x: int,
    work_line_end_y: int | None,
    line_color: str,
) -> Iterable[str]:
    line_start_y = markers[0][1]
    line_end_y = work_line_end_y if work_line_end_y is not None else markers[-1][1]
    yield (
        f'<line x1="{work_marker_x}" y1="{line_start_y}" '
        f'x2="{work_marker_x}" y2="{line_end_y}" '
        f'stroke="{line_color}" stroke-width="2"/>'
    )

    start_dates = [entry.start for entry, _ in markers]
    newest_start = start_dates[0]
    oldest_start = start_dates[-1]
    total_months = max(
        1,
        (newest_start.year - oldest_start.year) * 12
        + (newest_start.month - oldest_start.month),
    )
    vertical_span = max(1, line_end_y - line_start_y)
    for entry, _fallback_y in markers:
        months_from_latest = (
            (newest_start.year - entry.start.year) * 12
            + (newest_start.month - entry.start.month)
        )
        event_y = line_start_y + round((months_from_latest / total_months) * vertical_span)
        yield (
            f'<circle cx="{work_marker_x}" cy="{event_y}" '
            f'r="{WORK_MARKER_RADIUS}" class="{entry.marker_class}"/>'
        )
