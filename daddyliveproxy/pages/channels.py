from typing import List, TypedDict

import reflex as rx

from daddyliveproxy import backend
from daddyliveproxy.components import navbar


class ChannelItem(TypedDict):
    id: str
    name: str
    enabled: bool


class ChannelState(rx.State):
    channels: List[ChannelItem] = []
    search_query: str = ""

    @rx.var
    def filtered_channels(self) -> List[ChannelItem]:
        if not self.search_query:
            return self.channels
        return [
            ch
            for ch in self.channels
            if self.search_query.lower() in ch["name"].lower()
        ]

    async def on_load(self):
        selected = backend.get_selected_channel_ids()
        self.channels = [
            ChannelItem(id=ch.id, name=ch.name, enabled=(ch.id in selected))
            for ch in backend.get_channels()
        ]

    def set_channel(self, channel_id: str, value: bool):
        for ch in self.channels:
            if ch["id"] == channel_id:
                ch["enabled"] = value
                break

    def select_all(self):
        for ch in self.channels:
            ch["enabled"] = True

    def select_none(self):
        for ch in self.channels:
            ch["enabled"] = False

    async def save(self):
        ids = [ch["id"] for ch in self.channels if ch["enabled"]]
        try:
            backend.set_selected_channel_ids(ids)
        except Exception as exc:
            return rx.toast(f"Failed to save channels: {exc}", color_scheme="red")
        return rx.toast("Channel selection saved")


@rx.page(
    route="/channels",
    title="Daddy Live Proxy - Channels",
    description="A proxy for Daddy Live streams",
    on_load=ChannelState.on_load,
)
def channels() -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.center(
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.button(
                                "Select All",
                                on_click=ChannelState.select_all,
                                cursor="pointer",
                            ),
                            rx.button(
                                "Select None",
                                on_click=ChannelState.select_none,
                                color_scheme="gray",
                                cursor="pointer",
                            ),
                            rx.spacer(),
                            rx.button(
                                "Save",
                                on_click=ChannelState.save,
                                color_scheme="green",
                                cursor="pointer",
                            ),
                            width="100%",
                        ),
                        rx.divider(margin_y="1rem"),
                        rx.input(
                            rx.input.slot(rx.icon("search")),
                            placeholder="Search channels...",
                            on_change=ChannelState.set_search_query,
                            value=ChannelState.search_query,
                            width="100%",
                            margin_bottom="1rem",
                        ),
                        rx.scroll_area(
                            rx.grid(
                                rx.foreach(
                                    ChannelState.filtered_channels,
                                    lambda ch: rx.checkbox(
                                        ch["name"],
                                        checked=ch["enabled"],
                                        on_change=lambda v, cid=ch[
                                            "id"
                                        ]: ChannelState.set_channel(cid, v),
                                    ),
                                ),
                                grid_template_columns="repeat(auto-fill, minmax(200px, 1fr))",
                                spacing="2",
                                width="100%",
                            ),
                            height="60vh",
                            width="100%",
                        ),
                    ),
                    padding="2rem",
                    width="100%",
                    max_width="800px",
                    border_radius="xl",
                    box_shadow="lg",
                ),
                padding_y="3rem",
            ),
            padding_top="7rem",
        ),
    )
