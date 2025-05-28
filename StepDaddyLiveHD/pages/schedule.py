import reflex as rx
from typing import Dict, List, TypedDict
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from dateutil import parser
from StepDaddyLiveHD import backend
from StepDaddyLiveHD.components import navbar


class ChannelItem(TypedDict):
    name: str
    id: str


class EventItem(TypedDict):
    name: str
    time: str
    dt: datetime
    category: str
    channels: List[ChannelItem]


class ScheduleState(rx.State):
    events: List[EventItem] = []
    categories: Dict[str, bool] = {}
    switch: bool = True
    search_query: str = ""

    @staticmethod
    def get_channels(channels: dict) -> List[ChannelItem]:
        channel_list = []
        if isinstance(channels, list):
            for channel in channels:
                try:
                    channel_list.append(ChannelItem(name=channel["channel_name"], id=channel["channel_id"]))
                except:
                    continue
        elif isinstance(channels, dict):
            for channel_dic in channels:
                try:
                    channel_list.append(ChannelItem(name=channels[channel_dic]["channel_name"], id=channels[channel_dic]["channel_id"]))
                except:
                    continue
        return channel_list

    def toggle_category(self, category):
        self.categories[category] = not self.categories.get(category, False)

    def double_category(self, category):
        for cat in self.categories:
            if cat != category:
                self.categories[cat] = False
            else:
                self.categories[cat] = True

    async def on_load(self):
        self.events = []
        categories = {}
        days = await backend.get_schedule()
        for day in days:
            name = day.split(" - ")[0]
            dt = parser.parse(name, dayfirst=True)
            for category in days[day]:
                categories[category] = True
                for event in days[day][category]:
                    time = event["time"]
                    hour, minute = map(int, time.split(":"))
                    event_dt = dt.replace(hour=hour, minute=minute).replace(tzinfo=ZoneInfo("UTC"))
                    channels = self.get_channels(event.get("channels"))
                    channels.extend(self.get_channels(event.get("channels2")))
                    channels.sort(key=lambda channel: channel["name"])
                    self.events.append(EventItem(name=event["event"], time=time, dt=event_dt, category=category, channels=channels))
        self.categories = dict(sorted(categories.items()))
        self.events.sort(key=lambda event: event["dt"])

    @rx.event
    def set_switch(self, value: bool):
        self.switch = value

    @rx.var
    def filtered_events(self) -> List[EventItem]:
        now = datetime.now(ZoneInfo("UTC")) - timedelta(minutes=30)
        query = self.search_query.strip().lower()

        return [
            event for event in self.events
            if self.categories.get(event["category"], False)
               and (not self.switch or event["dt"] > now)
               and (query == "" or query in event["name"].lower())
        ]


def event_card(event: EventItem) -> rx.Component:
    return rx.card(
        rx.heading(event["name"]),
        rx.hstack(
            rx.moment(event["dt"], format="HH:mm", local=True),
            rx.moment(event["dt"], format="ddd MMM DD YYYY", local=True),
            rx.badge(event["category"], margin_top="0.2rem"),
        ),
        rx.hstack(
            rx.foreach(
                event["channels"],
                lambda channel: rx.button(channel["name"], variant="surface", color_scheme="gray", size="1", on_click=rx.redirect(f"/watch/{channel['id']}")),
            ),
            wrap="wrap",
            margin_top="0.5rem",
        ),
        width="100%",
    )


def category_badge(category) -> rx.Component:
    return rx.badge(
        category[0],
        color_scheme=rx.cond(
            category[1],
            "red",
            "gray",
        ),
        _hover={"color": "white"},
        style={"cursor": "pointer"},
        on_click=lambda: ScheduleState.toggle_category(category[0]),
        on_double_click=lambda: ScheduleState.double_category(category[0]),
        size="2",
    )


@rx.page("/schedule", on_load=ScheduleState.on_load)
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
                                rx.foreach(ScheduleState.categories, category_badge),
                                spacing="2",
                                wrap="wrap",
                                margin_top="0.7rem",
                            ),
                            rx.hstack(
                                rx.text("Hide past events"),
                                rx.switch(
                                    on_change=ScheduleState.set_switch,
                                    checked=ScheduleState.switch,
                                    margin_top="0.2rem"
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
