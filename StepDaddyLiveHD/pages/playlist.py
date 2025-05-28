import reflex as rx
from rxconfig import config
from StepDaddyLiveHD.components import navbar


@rx.page("/playlist")
def playlist() -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.center(
                rx.card(
                    rx.vstack(
                        rx.cond(
                            config.proxy_content,
                            rx.fragment(),
                            rx.card(
                                rx.hstack(
                                    rx.icon(
                                        "info",
                                    ),
                                    rx.text(
                                        "Proxy content is disabled on this instance. Some clients may not work.",
                                    ),
                                ),
                                width="100%",
                                background_color=rx.color("accent", 7),
                            ),
                        ),
                        rx.heading("Welcome to StepDaddyLiveHD", size="7", margin_bottom="1rem"),
                        rx.text(
                            "StepDaddyLiveHD allows you to watch various TV channels via IPTV. "
                            "You can download the playlist file below and use it with your favorite media player.",
                        ),

                        rx.divider(margin_y="1.5rem"),

                        rx.heading("How to Use", size="5", margin_bottom="0.5rem"),
                        rx.text(
                            "1. Copy the link below or download the playlist file",
                            margin_bottom="0.5rem",
                            font_weight="medium",
                        ),
                        rx.text(
                            "2. Open it with your preferred media player or IPTV app",
                            margin_bottom="1.5rem",
                            font_weight="medium",
                        ),

                        rx.hstack(
                            rx.button(
                                "Download Playlist",
                                rx.icon("download", margin_right="0.5rem"),
                                on_click=rx.redirect(f"{config.api_url}/playlist.m3u8", is_external=True),
                                size="3",
                            ),
                            rx.button(
                                "Copy Link",
                                rx.icon("clipboard", margin_right="0.5rem"),
                                on_click=[
                                    rx.set_clipboard(f"{config.api_url}/playlist.m3u8"),
                                    rx.toast("Playlist URL copied to clipboard!"),
                                ],
                                size="3",
                                # variant="soft",
                                color_scheme="gray",
                            ),
                            width="100%",
                            justify="center",
                            spacing="4",
                            margin_bottom="1rem",
                        ),

                        rx.box(
                            rx.text(
                                f"{config.api_url}/playlist.m3u8",
                                font_family="mono",
                                font_size="sm",
                            ),
                            padding="0.75rem",
                            background="gray.100",
                            border_radius="md",
                            width="100%",
                            text_align="center",
                        ),

                        rx.divider(margin_y="1rem"),

                        rx.heading("Compatible Players", size="5", margin_bottom="1rem"),
                        rx.text(
                            "You can use the m3u8 playlist with most media players and IPTV applications:",
                            margin_bottom="1rem",
                        ),
                        rx.card(
                            rx.vstack(
                                rx.heading("VLC Media Player", size="6"),
                                rx.text("Popular free and open-source media player"),
                                rx.spacer(),
                                rx.link(
                                    "Download",
                                    href="https://www.videolan.org/vlc/",
                                    target="_blank",
                                    color="blue.500",
                                ),
                                height="100%",
                                justify="between",
                                align="center",
                            ),
                            padding="1rem",
                            width="100%",
                        ),

                        rx.card(
                            rx.vstack(
                                rx.heading("IPTVnator", size="6"),
                                rx.text("Cross-platform IPTV player application"),
                                rx.spacer(),
                                rx.link(
                                    "Download",
                                    href="https://github.com/4gray/iptvnator",
                                    target="_blank",
                                    color="blue.500",
                                ),
                                height="100%",
                                justify="between",
                                align="center",
                            ),
                            padding="1rem",
                            width="100%",
                        ),

                        rx.card(
                            rx.vstack(
                                rx.heading("Jellyfin", size="6"),
                                rx.text("Free media system to manage your media"),
                                rx.spacer(),
                                rx.link(
                                    "Download",
                                    href="https://jellyfin.org/",
                                    target="_blank",
                                    color="blue.500",
                                ),
                                height="100%",
                                justify="between",
                                align="center",
                            ),
                            padding="1rem",
                            width="100%",
                        ),

                        rx.divider(margin_y="1rem"),

                        rx.text(
                            "Need help? Most media players allow you to open network streams or IPTV playlists. "
                            "Simply paste the m3u8 URL above or import the downloaded playlist file.",
                            font_style="italic",
                            color="gray.600",
                            text_align="center",
                        ),
                        spacing="4",
                        width="100%",
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
