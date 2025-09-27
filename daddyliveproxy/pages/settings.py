import json
from pathlib import Path

import reflex as rx

import daddyliveproxy as dlp
from daddyliveproxy import backend
from daddyliveproxy.components import navbar
from daddyliveproxy.logging import get_logger
from rxconfig import config

SETTINGS_PATH = Path(dlp.__file__).with_name("settings.json")

ALLOWED_PREFIXES = {"stream", "cast", "watch", "player", "casting"}

logger = get_logger("settings")


class SettingsState(rx.State):
    base_url: str = ""
    selected_prefix: str = "stream"

    def load_settings(self):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = json.load(f)
            self.base_url = settings.get("base_url", "")
            self.selected_prefix = settings.get("prefix", "stream")
        except Exception as e:
            print(f"Error loading settings: {e}")

    async def save_settings(self):
        # Normalize/Sanitize
        base_url = (self.base_url or "").strip().rstrip("/")
        prefix = (self.selected_prefix or "stream").strip().lower()
        if prefix not in ALLOWED_PREFIXES:
            return rx.toast.error(f"Invalid prefix: {prefix}")

        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            return rx.toast.error("Base URL must start with http:// or https://")

        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump({"base_url": base_url, "prefix": prefix}, f, indent=4)

            # Log on save (you'll also see server-side logs if you added the backend logger)
            logger.info(
                "Settings saved from UI: base_url=%s, prefix=%s", base_url, prefix
            )

            # Immediately refresh channels so new settings take effect
            await backend.refresh_all()

            return rx.toast.info("Settings saved and channels refreshed!")
        except Exception as e:
            return rx.toast.error(f"Error saving settings: {e}")


@rx.page(
    route="/settings",
    title="Daddy Live Proxy - Settings",
    description="A proxy for Daddy Live streams",
    on_load=SettingsState.load_settings,
)
def settings() -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.center(
                rx.card(
                    rx.vstack(
                        # Warning if proxy_content disabled
                        rx.cond(
                            config.proxy_content,
                            rx.fragment(),
                            rx.card(
                                rx.hstack(
                                    rx.icon("info"),
                                    rx.text(
                                        "Proxy content is disabled on this instance. Some clients may not work.",
                                    ),
                                ),
                                width="100%",
                                background_color=rx.color("accent", 7),
                            ),
                        ),
                        rx.heading(
                            "Welcome to daddyliveproxy", size="7", margin_bottom="1rem"
                        ),
                        rx.text(
                            "This proxy allows you to watch various TV channels via IPTV. "
                            "You can download the playlist file below and use it with your favorite media player.",
                        ),
                        rx.divider(margin_y="1.5rem"),
                        # Settings Form
                        rx.heading("Settings", size="5", margin_bottom="1rem"),
                        rx.text("URL:"),
                        rx.input(
                            value=SettingsState.base_url,
                            on_change=SettingsState.set_base_url,
                            placeholder="Enter the base URL",
                            width="100%",
                        ),
                        rx.text("Prefix:", margin_top="1rem"),
                        rx.select(
                            ["stream", "cast", "watch", "player", "casting"],
                            value=SettingsState.selected_prefix,
                            on_change=SettingsState.set_selected_prefix,
                            width="100%",
                        ),
                        rx.button(
                            "Save",
                            on_click=SettingsState.save_settings,
                            margin_top="1.5rem",
                            width="100%",
                            cursor="pointer",
                        ),
                        rx.divider(margin_y="1.5rem"),
                        # === Playlist section ===
                        rx.heading("Playlist", size="5", margin_bottom="0.5rem"),
                        rx.text(
                            "You can download the M3U8 playlist file below to use with compatible media players. Use localhost or your server IP if running locally.",
                            margin_bottom="0.5rem",
                        ),
                        rx.hstack(
                            rx.link(
                                rx.button(
                                    "Download Playlist",
                                    rx.icon("download", margin_right="0.5rem"),
                                    size="3",
                                    cursor="pointer",
                                ),
                                href=f"{config.api_url}/playlist.m3u8?download=1",
                                is_external=True,
                            ),
                            rx.button(
                                "Copy Playlist URL",
                                rx.icon("clipboard", margin_right="0.5rem"),
                                on_click=[
                                    rx.set_clipboard(f"{config.api_url}/playlist.m3u8"),
                                    rx.toast("Playlist URL copied to clipboard!"),
                                ],
                                size="3",
                                color_scheme="gray",
                                cursor="pointer",
                            ),
                            width="100%",
                            justify="center",
                            spacing="4",
                            margin_bottom="0.75rem",
                        ),
                        rx.box(
                            rx.text(
                                f"{config.api_url}/playlist.m3u8",
                                font_family="mono",
                                font_size="sm",
                            ),
                            padding="0.5rem",
                            background="gray.100",
                            border_radius="md",
                            width="100%",
                            text_align="center",
                        ),
                        rx.divider(margin_y="1rem"),
                        # === Guide section ===
                        rx.heading("Guide", size="5", margin_bottom="0.5rem"),
                        rx.text(
                            "You can download the XMLTV guide file below to use with compatible media players. Use localhost or your server IP if running locally.",
                            margin_bottom="0.5rem",
                        ),
                        rx.hstack(
                            rx.link(
                                rx.button(
                                    "Download Guide",
                                    rx.icon("download", margin_right="0.5rem"),
                                    size="3",
                                    cursor="pointer",
                                ),
                                href=f"{config.api_url}/guide.xml?download=1",
                                is_external=True,
                            ),
                            rx.button(
                                "Copy Guide URL",
                                rx.icon("clipboard", margin_right="0.5rem"),
                                on_click=[
                                    rx.set_clipboard(f"{config.api_url}/guide.xml"),
                                    rx.toast("Guide URL copied to clipboard!"),
                                ],
                                size="3",
                                color_scheme="gray",
                                cursor="pointer",
                            ),
                            width="100%",
                            justify="center",
                            spacing="4",
                            margin_bottom="0.75rem",
                        ),
                        rx.box(
                            rx.text(
                                f"{config.api_url}/guide.xml",
                                font_family="mono",
                                font_size="sm",
                            ),
                            padding="0.5rem",
                            background="gray.100",
                            border_radius="md",
                            width="100%",
                            text_align="center",
                        ),
                        rx.divider(margin_y="1rem"),
                        # Compatible Players
                        rx.heading(
                            "Compatible Players", size="5", margin_bottom="1rem"
                        ),
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
