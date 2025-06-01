import reflex as rx
import StepDaddyLiveHD.pages
from typing import List, Optional
from StepDaddyLiveHD import backend
from StepDaddyLiveHD.components import navbar, card
from StepDaddyLiveHD.step_daddy import Channel


class State(rx.State):
    channels: List[Channel] = []
    search_query: str = ""
    selected_country: Optional[str] = None

    @rx.var
    def available_countries(self) -> List[str]:
        countries = set()
        for channel in self.channels:
            if channel.country and channel.country_flag:
                countries.add(f"{channel.country_flag} {channel.country}")
        return sorted(list(countries))

    @rx.var
    def filtered_channels(self) -> List[Channel]:
        filtered = self.channels
        if self.search_query:
            filtered = [ch for ch in filtered if self.search_query.lower() in ch.name.lower()]
        if self.selected_country:
            country_name = self.selected_country.split(" ", 1)[1] if " " in self.selected_country else self.selected_country
            filtered = [ch for ch in filtered if ch.country == country_name]
        return filtered

    async def on_load(self):
        self.channels = backend.get_channels()


def search_component() -> rx.Component:
    return rx.hstack(
        rx.input(
            rx.input.slot(
                rx.icon("search"),
            ),
            placeholder="Search channels...",
            on_change=State.set_search_query,
            value=State.search_query,
            width="100%",
            max_width="25rem",
            size="3",
        ),
        rx.select(
            State.available_countries,
            placeholder="Filter by country",
            on_change=State.set_selected_country,
            value=State.selected_country,
            size="3",
            width="12rem",
        ),
        spacing="4",
    )


@rx.page("/", on_load=State.on_load)
def index() -> rx.Component:
    return rx.box(
        navbar(search_component()),
        rx.center(
            rx.cond(
                State.channels,
                rx.grid(
                    rx.foreach(
                        State.filtered_channels,
                        lambda channel: card(channel),
                    ),
                    grid_template_columns="repeat(auto-fill, minmax(250px, 1fr))",
                    spacing=rx.breakpoints(
                        initial="4",
                        sm="6",
                        lg="9"
                    ),
                    width="100%",
                ),
                rx.center(
                    rx.spinner(),
                    height="50vh",
                ),
            ),
            padding="1rem",
            padding_top="10rem",
        ),
    )


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="red",
    ),
    api_transformer=backend.fastapi_app,
)

app.register_lifespan_task(backend.update_channels)