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
    shared_summary: bool = False


SectionItem = Line | WorkEntry


@dataclass
class Section:
    header: str
    lines: list[SectionItem]


def parse_work_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m").date()


def get_work_lines(section: dict[str, dict]) -> list[WorkEntry]:
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

    previous_summary = None
    for entry in entries:
        if entry.summary and entry.summary == previous_summary:
            entry.summary = ""
            entry.shared_summary = True
        elif entry.summary:
            previous_summary = entry.summary

    return entries


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
            yield Section(category, list(get_work_lines(section)))
            continue
        yield Section(category, list(get_lines(section)))
