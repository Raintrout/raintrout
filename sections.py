from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterator


@dataclass
class Line:
    key: list[str]
    value: str


@dataclass
class WorkEntry:
    key: list[str]
    summary: str
    marker_class: str
    start: date


@dataclass
class WorkBlock:
    """A work entry plus any consecutive entries that share its summary."""
    primary: WorkEntry
    followers: list[WorkEntry]


SectionItem = Line | WorkBlock


@dataclass
class Section:
    header: str
    lines: list[SectionItem]


def parse_work_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m").date()


def get_work_blocks(section: dict[str, dict]) -> list[WorkBlock]:
    entries = [
        WorkEntry(
            key=[label],
            summary=details.get("summary", ""),
            marker_class="currentWorkColor" if details.get("end") is None else "pastWorkColor",
            start=parse_work_date(details["start"]),
        )
        for label, details in section.items()
    ]
    entries.sort(key=lambda entry: entry.start, reverse=True)

    blocks: list[WorkBlock] = []
    for entry in entries:
        if blocks and entry.summary and entry.summary == blocks[-1].primary.summary:
            blocks[-1].followers.append(entry)
        else:
            blocks.append(WorkBlock(primary=entry, followers=[]))

    return blocks


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


def get_sections(profile: dict) -> Iterator[Section]:
    for category, section in profile.items():
        if category == "Work" and isinstance(section, dict):
            yield Section(category, list(get_work_blocks(section)))
            continue
        yield Section(category, list(get_lines(section)))
