from dataclasses import dataclass
from datetime import date, datetime
from math import ceil
from typing import Iterable, Iterator

LOW_CONTEXT_TRAILING_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}

@dataclass
class Line:
    key: list[str]
    value: str


@dataclass
class Section:
    header: str
    lines: list[Line]


@dataclass
class WorkEntry:
    key: list[str]
    summary: str
    marker_class: str
    start: date
    shared_summary: bool = False


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


def render_key(keys: list[str]) -> str:
    return '.'.join(f'<tspan class="key">{key}</tspan>' for key in keys)


def parse_work_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m").date()


def get_work_lines(section: dict[str, dict]) -> list[WorkEntry]:
    entries = []

    for label, details in section.items():
        entries.append(
            WorkEntry(
                key=[label],
                summary=details.get("summary", ""),
                marker_class="currentWorkColor" if details.get("end") is None else "pastWorkColor",
                start=parse_work_date(details["start"]),
            )
        )

    entries = sorted(entries, key=lambda entry: entry.start, reverse=True)

    previous_summary = None
    for entry in entries:
        if entry.summary and entry.summary == previous_summary:
            entry.summary = ""
            entry.shared_summary = True
        elif entry.summary:
            previous_summary = entry.summary

    return entries


def render(
    sections: Iterable[Section],
    offset_x: int = 390,
    offset_y: int = 30,
    line_length: int = 60,
    line_height: int = 20,
    max_y: int = 510,
    overlay_elements: list[str] | None = None,
    work_timeline_line_color: str = "#616e7f",
) -> Iterator[str]:
    for i, section in enumerate(sections):
        if i == 0:
            yield f'<tspan x="{offset_x}" y="{offset_y}">{section.header}</tspan> {"—"*(line_length-1-len(section.header))}'
        else:
            yield f'<tspan x="{offset_x}" y="{offset_y}">- {section.header}</tspan> {"—"*(line_length-3-len(section.header))}'
        offset_y += line_height
        work_marker_x = offset_x + 8
        work_text_x = offset_x + 20
        work_line_length = line_length
        work_entry_markers = []
        work_line_end_y = None

        line_index = 0
        while line_index < len(section.lines):
            line = section.lines[line_index]
            if isinstance(line, WorkEntry):
                work_entry_markers.append((line, offset_y - 6))
                key = '.'.join(line.key)
                value = line.summary
                shared_line = None

                if (
                    line_index + 1 < len(section.lines)
                    and isinstance(section.lines[line_index + 1], WorkEntry)
                    and section.lines[line_index + 1].shared_summary
                ):
                    shared_line = section.lines[line_index + 1]

                if line.shared_summary:
                    yield f'<tspan x="{work_text_x}" y="{offset_y}">{render_key(line.key)}</tspan>'
                    offset_y += line_height
                    line_index += 1
                elif len(value) + len(key) > work_line_length - 10:
                    for value_index, value_part in enumerate(split_value(value, work_line_length - 4 - len(key))):
                        if value_index == 0:
                            dots = "." * max(1, work_line_length - 4 - len(key) - len(value_part))
                            yield f'<tspan x="{work_text_x}" y="{offset_y}">{render_key(line.key)}</tspan><tspan class="cc"> {dots} </tspan><tspan class="value">{value_part}</tspan>'
                        else:
                            if value_index == 1 and shared_line is not None:
                                shared_key = ".".join(shared_line.key)
                                work_entry_markers.append((shared_line, offset_y - 6))
                                gap = " " * max(1, work_line_length - 4 - len(shared_key) - len(value_part))
                                yield f'<tspan x="{work_text_x}" y="{offset_y}">{render_key(shared_line.key)}</tspan><tspan class="cc" xml:space="preserve"> {gap} </tspan><tspan class="value">{value_part}</tspan>'
                            else:
                                gap = " " * max(1, work_line_length - 4 - len(value_part))
                                yield f'<tspan x="{work_text_x}" y="{offset_y}" class="cc" xml:space="preserve"> {gap} </tspan><tspan class="value">{value_part}</tspan>'
                        offset_y += line_height
                    line_index += 2 if shared_line is not None else 1
                else:
                    dots = "." * max(1, work_line_length - 4 - len(key) - len(value))
                    yield f'<tspan x="{work_text_x}" y="{offset_y}">{render_key(line.key)}</tspan><tspan class="cc"> {dots} </tspan><tspan class="value">{value}</tspan>'
                    offset_y += line_height
                    line_index += 1
                work_line_end_y = offset_y - 6
                continue

            key = '.'.join(line.key)
            value = line.value
            if len(value) + len(key) > line_length - 10:
                for i, value in enumerate(split_value(value, line_length-5-len(key))):
                    if i == 0:
                        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>{render_key(line.key)}:<tspan class="cc"> {"."*(line_length-5-len(key)-len(value))} </tspan><tspan class="value">{value}</tspan>'
                    else:
                        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan><tspan class="cc"> {"."*(line_length-5-len(value))} </tspan><tspan class="value">{value}</tspan>'
                    offset_y += line_height
            else:
                yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>{render_key(line.key)}:<tspan class="cc"> {"."*(line_length-5-len(key)-len(value))} </tspan><tspan class="value">{value}</tspan>'
                offset_y += line_height
            line_index += 1

        yield f'<tspan x="{offset_x}" y="{offset_y}"></tspan>'
        offset_y += line_height

        if section.header == "Work" and overlay_elements is not None and work_entry_markers:
            line_start_y = work_entry_markers[0][1]
            line_end_y = work_line_end_y or work_entry_markers[-1][1]
            overlay_elements.append(
                f'<line x1="{work_marker_x}" y1="{line_start_y}" x2="{work_marker_x}" y2="{line_end_y}" stroke="{work_timeline_line_color}" stroke-width="2"/>'
            )
            start_dates = [entry.start for entry, _ in work_entry_markers]
            newest_start = start_dates[0]
            oldest_start = start_dates[-1]
            total_months = max(
                1,
                (newest_start.year - oldest_start.year) * 12
                + (newest_start.month - oldest_start.month),
            )
            vertical_span = max(1, line_end_y - line_start_y)
            for work_entry, fallback_y in work_entry_markers:
                months_from_latest = (
                    (newest_start.year - work_entry.start.year) * 12
                    + (newest_start.month - work_entry.start.month)
                )
                event_y = line_start_y + round((months_from_latest / total_months) * vertical_span)
                overlay_elements.append(
                    f'<circle cx="{work_marker_x}" cy="{event_y}" r="4" class="{work_entry.marker_class}"/>'
                )
    
    while offset_y <= max_y:
        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>'
        offset_y += line_height


def get_lines(section: dict, keys: list[str] | None = None) -> Iterator[Line]:
    keys = keys or []
    for key, value in section.items():
        key_list = keys + [key]

        if isinstance(value, dict):
            yield from get_lines(value, keys=key_list)
        elif isinstance(value, list):
            yield Line(key_list, ', '.join(value))
        elif value is None:
            yield Line(key_list, "")
        else:
            yield Line(key_list, value)


def get_sections(about: dict) -> Iterator[Section]:
    for category, section in about.items():
        if str(category).startswith("_"):
            continue
        if category == "Work" and isinstance(section, dict):
            yield Section(category, get_work_lines(section))
            continue
        lines = list(get_lines(section))
        yield Section(category, lines)
