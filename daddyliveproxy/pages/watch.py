from __future__ import annotations

from typing import Any, Optional

import reflex as rx

from daddyliveproxy import backend
from daddyliveproxy.components import MediaPlayer, navbar
from daddyliveproxy.step_daddy import Channel
from rxconfig import config

media_player = MediaPlayer.create


class WatchState(rx.State):
    """State for the channel watch page."""

    @rx.var
    def channel(self) -> Optional[Channel]:
        channel_id = self.channel_id
        if not channel_id:
            return None
        return backend.get_channel(channel_id)

    @rx.var
    def has_channel(self) -> bool:
        return self.channel is not None

    @rx.var
    def url(self) -> str:
        channel_id = self.channel_id
        if not channel_id:
            return ""
        return f"{config.api_url}/stream/{channel_id}.m3u8"

    @rx.var
    def is_loading(self) -> bool:
        return not backend.get_channels()


def player_buttons(**props: Any) -> rx.Component:
    """Render buttons for opening the stream in external players."""
    return rx.hstack(
        rx.button(
            rx.text("VLC"),
            rx.icon("external-link", size=15),
            on_click=rx.redirect(f"vlc://{WatchState.url}", is_external=True),
            size="1",
            color_scheme="orange",
            variant="soft",
            high_contrast=True,
            cursor="pointer",
        ),
        rx.button(
            rx.text("MPV"),
            rx.icon("external-link", size=15),
            on_click=rx.redirect(f"mpv://{WatchState.url}", is_external=True),
            size="1",
            color_scheme="purple",
            variant="soft",
            high_contrast=True,
            cursor="pointer",
        ),
        rx.button(
            rx.text("Pot"),
            rx.icon("external-link", size=15),
            on_click=rx.redirect(f"potplayer://{WatchState.url}", is_external=True),
            size="1",
            color_scheme="yellow",
            variant="soft",
            high_contrast=True,
            cursor="pointer",
        ),
        **props,
    )


def uri_card() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.button(
                rx.text(WatchState.url),
                rx.icon("link-2", size=20),
                on_click=[
                    rx.set_clipboard(WatchState.url),
                    rx.toast("Copied to clipboard!"),
                ],
                size="1",
                variant="surface",
                radius="full",
                color_scheme="gray",
                cursor="pointer",
            ),
            rx.spacer(),
            player_buttons(wrap="wrap"),
        ),
        margin_top="1rem",
    )


@rx.page(
    route="/watch/[channel_id]",
    title="Daddy Live Proxy - Watch",
    description="A proxy for Daddy Live streams",
)
def watch() -> rx.Component:
    warning = rx.cond(
        config.proxy_content,
        rx.fragment(),
        rx.card(
            rx.hstack(
                rx.icon("info"),
                rx.text(
                    "Proxy content is disabled on this instance. Web player may not work due to CORS.",
                ),
            ),
            width="100%",
            margin_bottom="1rem",
            background_color=rx.color("accent", 7),
        ),
    )

    channel_header = rx.hstack(
        rx.box(
            rx.hstack(
                rx.card(
                    rx.image(
                        src=WatchState.channel.logo,
                        width="60px",
                        height="60px",
                        object_fit="contain",
                    ),
                    padding="0",
                ),
                rx.box(
                    rx.heading(
                        WatchState.channel.name,
                        margin_bottom="0.3rem",
                        padding_top="0.2rem",
                    ),
                    rx.box(
                        rx.hstack(
                            rx.cond(
                                WatchState.channel.tags,
                                rx.foreach(
                                    WatchState.channel.tags,
                                    lambda tag: rx.badge(
                                        tag, variant="surface", color_scheme="gray"
                                    ),
                                ),
                            ),
                        ),
                    ),
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
            ),
            flex="1",
            min_width="0",
        ),
        rx.tablet_and_desktop(
            rx.box(
                rx.vstack(
                    rx.button(
                        rx.text(
                            WatchState.url,
                            overflow="hidden",
                            text_overflow="ellipsis",
                            white_space="nowrap",
                        ),
                        rx.icon("link-2", size=20),
                        on_click=[
                            rx.set_clipboard(WatchState.url),
                            rx.toast("Copied to clipboard!"),
                        ],
                        size="1",
                        variant="surface",
                        radius="full",
                        color_scheme="gray",
                        cursor="pointer",
                    ),
                    rx.hstack(
                        rx.spacer(),
                        player_buttons(wrap="wrap"),
                        width="100%",
                    ),
                ),
                width="100%",
                flex="1",
                min_width="0",
            ),
        ),
        justify="between",
        align="start",
        padding_bottom="0.5rem",
        width="100%",
    )

    channel_player = rx.box(
        media_player(
            title=WatchState.channel.name,
            src=WatchState.url,
        ),
        width="100%",
    )

    unavailable = rx.vstack(
        rx.icon("triangle_alert", size=32),
        rx.heading("Channel unavailable", size="5"),
        rx.text(
            "This channel could not be found. Please return to the channel list.",
            align="center",
        ),
        rx.link("Go back to channels", href="/", color="accent.9"),
        spacing="2",
        align="center",
        padding_y="2rem",
    )

    card_body = rx.cond(
        WatchState.has_channel,
        rx.vstack(channel_header, channel_player),
        rx.cond(
            WatchState.is_loading,
            rx.center(rx.spinner(size="3"), height="200px"),
            unavailable,
        ),
    )

    return rx.box(
        navbar(),
        rx.container(
            warning,
            rx.center(
                rx.card(
                    card_body,
                    padding_bottom="0.3rem",
                    width="100%",
                ),
                width="100%",
            ),
            rx.mobile_only(
                rx.cond(
                    WatchState.has_channel,
                    uri_card(),
                    rx.fragment(),
                ),
            ),
            size="4",
            padding_top="10rem",
        ),
    )
