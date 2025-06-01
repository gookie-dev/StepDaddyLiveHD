import reflex as rx
from StepDaddyLiveHD.step_daddy import Channel


def card(channel: Channel) -> rx.Component:
    return rx.link(
        rx.box(
            rx.image(
                src=channel.logo,
                position="absolute",
                width="100%",
                height="100%",
                object_fit="cover",
                filter="blur(10px)",
                opacity="0.4",
                z_index="0",
                padding="1rem",
                loading="lazy",
            ),
            rx.card(
                rx.box(
                    rx.separator(
                        position="absolute",
                        top="32px",
                        left="0",
                        width="calc(50% - 35px)",
                    ),
                    rx.separator(
                        position="absolute",
                        top="32px",
                        right="0",
                        width="calc(50% - 35px)",
                    ),
                    rx.center(
                        rx.image(
                            src=channel.logo,
                            width="64px",
                            height="64px",
                            object_fit="contain",
                            position="relative",
                            border_radius="8px",
                            loading="lazy",
                        ),
                    ),
                    position="relative",
                ),
                rx.center(
                    rx.box(
                        rx.heading(
                            rx.cond(
                                channel.country_flag,
                                rx.text(
                                    channel.country_flag,
                                    " ",
                                    channel.name,
                                ),
                                channel.name,
                            ),
                            color="white",
                            align="center",
                        ),
                        padding_top="0.7rem",
                        padding_bottom="3rem",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                        width="100%",
                    ),
                    rx.flex(
                        rx.cond(
                            channel.tags,
                            rx.foreach(
                                channel.tags,
                                lambda tag: rx.badge(tag, variant="surface", color_scheme="gray")
                            ),
                        ),
                        spacing=rx.breakpoints(
                            initial="2",
                            sm="1",
                            lg="3",
                        ),
                        position="absolute",
                        bottom="8px",
                    ),
                    position="relative",
                    width="100%",
                ),
                z_index="1",
                position="relative",
                background="rgba(26, 25, 27, 0.8)",
                border="2px solid transparent",
                style={
                    "_hover": {
                        "border": "2px solid #fa5252",
                    }
                },
            ),
            position="relative",
        ),
        href=f"/watch/{channel.id}",
    )