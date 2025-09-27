from datetime import datetime, timedelta
from typing import Dict, List, TypedDict
from zoneinfo import ZoneInfo

import reflex as rx
from dateutil import parser

from daddyliveproxy import backend
from daddyliveproxy.components import navbar
from daddyliveproxy.logging import get_logger
from rxconfig import config

logger = get_logger("schedule")


class ChannelItem(TypedDict):
    name: str
    id: str


class EventItem(TypedDict):
    name: str
    time: str
    date: str
    dt: datetime
    category: str
    channels: List[ChannelItem]


class CategoryFilter(TypedDict):
    name: str
    selected: bool


class ScheduleState(rx.State):
    """State management for the schedule page."""

    events: List[EventItem] = []
    categories: Dict[str, bool] = {}
    switch: bool = True
    search_query: str = ""

    @staticmethod
    def get_channels(channels: object) -> List[ChannelItem]:
        """Normalise the channel data returned by the schedule API."""

        channel_list: List[ChannelItem] = []
        if isinstance(channels, list):
            iterable = channels
        elif isinstance(channels, dict):
            iterable = channels.values()
        else:
            return channel_list

        for channel in iterable:
            if not isinstance(channel, dict):
                continue
            name = channel.get("channel_name")
            cid = channel.get("channel_id")
            if not name or not cid:
                continue
            channel_list.append(ChannelItem(name=str(name), id=str(cid)))
        return channel_list

    @rx.event
    def toggle_category(self, category: str) -> None:
        """Toggle the given category filter."""

        self.categories[category] = not self.categories.get(category, False)

    @rx.event
    def double_category(self, category: str) -> None:
        """Enable only the selected category."""

        for cat in self.categories:
            self.categories[cat] = cat == category

    @rx.event
    def set_search_query(self, value: str) -> None:
        """Update the event search query."""

        self.search_query = value

    async def on_load(self):
        self.events = []
        categories: Dict[str, bool] = {}
        schedule = await backend.get_schedule()
        if not isinstance(schedule, dict):
            logger.warning("Schedule payload was not a dictionary: %s", type(schedule))
            self.categories = {}
            return

        tz = ZoneInfo(config.timezone)
        utc = ZoneInfo("UTC")

        for day, groups in schedule.items():
            if not isinstance(groups, dict):
                continue
            name = str(day).split(" - ")[0]
            try:
                dt = parser.parse(name, dayfirst=True)
            except (ValueError, TypeError) as exc:
                logger.debug("Skipping schedule day %s: %s", day, exc)
                continue

            for category, events in groups.items():
                categories.setdefault(category, False)
                if not isinstance(events, list):
                    continue
                for event in events:
                    if not isinstance(event, dict):
                        continue
                    time_utc = event.get("time")
                    if not time_utc:
                        continue
                    try:
                        hour, minute = map(int, str(time_utc).split(":"))
                    except ValueError:
                        logger.debug("Invalid event time '%s'", time_utc)
                        continue
                    event_dt = dt.replace(
                        hour=hour, minute=minute, tzinfo=utc
                    ).astimezone(tz)
                    channels = self.get_channels(event.get("channels"))
                    channels.extend(self.get_channels(event.get("channels2")))
                    channels.sort(key=lambda channel: channel["name"])
                    date_str = event_dt.strftime("%a %b %d %Y")
                    self.events.append(
                        EventItem(
                            name=str(event.get("event") or "Unknown"),
                            time=event_dt.strftime("%H:%M"),
                            date=date_str,
                            dt=event_dt,
                            category=str(category),
                            channels=channels,
                        )
                    )

        self.categories = dict(sorted(categories.items()))
        self.events.sort(key=lambda event: event["dt"])

    @rx.event
    def set_switch(self, value: bool):
        self.switch = value

    @rx.var
    def filtered_events(self) -> List[EventItem]:
        now = datetime.now(ZoneInfo(config.timezone)) - timedelta(minutes=30)
        query = self.search_query.strip().lower()

        active = [cat for cat, selected in self.categories.items() if selected]

        return [
            event
            for event in self.events
            if (not active or event["category"] in active)
            and (not self.switch or event["dt"] > now)
            and (query == "" or query in event["name"].lower())
        ]

    @rx.var
    def category_filters(self) -> List[CategoryFilter]:
        return [
            CategoryFilter(name=name, selected=selected)
            for name, selected in self.categories.items()
        ]


def event_card(event: EventItem) -> rx.Component:
    """Render a single schedule entry."""
    return rx.card(
        rx.heading(event["name"]),
        rx.hstack(
            rx.text(event["time"]),
            rx.text(event["date"]),
            rx.badge(event["category"], margin_top="0.2rem"),
        ),
        rx.hstack(
            rx.foreach(
                event["channels"],
                lambda channel: rx.button(
                    channel["name"],
                    variant="surface",
                    color_scheme="gray",
                    size="1",
                    on_click=rx.redirect(f"/watch/{channel['id']}"),
                    cursor="pointer",
                ),
            ),
            wrap="wrap",
            margin_top="0.5rem",
        ),
        width="100%",
    )


def category_badge(category: CategoryFilter) -> rx.Component:
    """Render an interactive filter badge for a category."""

    name = category["name"]
    selected = category["selected"]
    return rx.badge(
        name,
        color_scheme=rx.cond(selected, "red", "gray"),
        _hover={"color": "white"},
        style={"cursor": "pointer"},
        on_click=lambda: ScheduleState.toggle_category(name),
        on_double_click=lambda: ScheduleState.double_category(name),
        size="2",
    )


@rx.page(
    route="/schedule",
    title="Daddy Live Proxy - Schedule",
    description="A proxy for Daddy Live streams",
    on_load=ScheduleState.on_load,
)
def schedule() -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.center(
                rx.vstack(
                    rx.cond(
                        ScheduleState.categories,
                        rx.card(
                            rx.input(
                                placeholder="Search events...",
                                on_change=ScheduleState.set_search_query,
                                value=ScheduleState.search_query,
                                width="100%",
                                size="3",
                            ),
                            rx.hstack(
                                rx.text("Filter by tag:"),
                                rx.foreach(
                                    ScheduleState.category_filters, category_badge
                                ),
                                spacing="2",
                                wrap="wrap",
                                margin_top="0.7rem",
                            ),
                            rx.hstack(
                                rx.text("Hide past events"),
                                rx.switch(
                                    on_change=ScheduleState.set_switch,
                                    checked=ScheduleState.switch,
                                    margin_top="0.2rem",
                                ),
                                margin_top="0.5rem",
                            ),
                        ),
                        rx.spinner(size="3"),
                    ),
                    rx.foreach(ScheduleState.filtered_events, event_card),
                ),
            ),
            padding_top="10rem",
        ),
    )
