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
                                        "El contenido proxy está deshabilitado en esta instancia. Algunos clientes pueden no funcionar.",
                                    ),
                                ),
                                width="100%",
                                background_color=rx.color("accent", 7),
                            ),
                        ),
                        rx.heading("Bienvenido a StepDaddyLiveHD", size="7", margin_bottom="1rem"),
                        rx.text(
                            "StepDaddyLiveHD te permite ver diversos canales de TV vía IPTV. "
                            "Puedes descargar el archivo de lista de reproducción más abajo y usarlo con tu reproductor multimedia favorito.",
                        ),

                        rx.divider(margin_y="1.5rem"),

                        rx.heading("Cómo usar", size="5", margin_bottom="0.5rem"),
                        rx.text(
                            "1. Copia el enlace de abajo o descarga el archivo de la lista de reproducción",
                            margin_bottom="0.5rem",
                            font_weight="medium",
                        ),
                        rx.text(
                            "2. Ábrelo con tu reproductor multimedia o aplicación de IPTV preferida",
                            margin_bottom="1.5rem",
                            font_weight="medium",
                        ),

                        rx.hstack(
                            rx.button(
                                "Descargar lista de reproducción",
                                rx.icon("download", margin_right="0.5rem"),
                                on_click=rx.redirect(f"{config.api_url}/playlist.m3u8", is_external=True),
                                size="3",
                            ),
                            rx.button(
                                "Copiar enlace",
                                rx.icon("clipboard", margin_right="0.5rem"),
                                on_click=[
                                    rx.set_clipboard(f"{config.api_url}/playlist.m3u8"),
                                    rx.toast("¡URL de la lista copiada en el portapapeles!"),
                                ],
                                size="3",
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

                        rx.heading("Reproductores compatibles", size="5", margin_bottom="1rem"),
                        rx.text(
                            "Puedes usar la lista m3u8 con la mayoría de reproductores multimedia y aplicaciones de IPTV:",
                            margin_bottom="1rem",
                        ),
                        rx.card(
                            rx.vstack(
                                rx.heading("VLC Media Player", size="6"),
                                rx.text("Reproductor multimedia gratuito y de código abierto muy popular"),
                                rx.spacer(),
                                rx.link(
                                    "Descargar",
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
                                rx.text("Aplicación de reproductor IPTV multiplataforma"),
                                rx.spacer(),
                                rx.link(
                                    "Descargar",
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
                                rx.text("Sistema multimedia gratuito para gestionar tus archivos"),
                                rx.spacer(),
                                rx.link(
                                    "Descargar",
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
                            "¿Necesitas ayuda? La mayoría de reproductores multimedia permiten abrir transmisiones en red o listas de IPTV. "
                            "Simplemente pega la URL m3u8 anterior o importa el archivo descargado.",
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
