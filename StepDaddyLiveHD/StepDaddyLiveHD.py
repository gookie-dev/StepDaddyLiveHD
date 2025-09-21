import reflex as rx
import StepDaddyLiveHD.pages
from typing import List
from StepDaddyLiveHD import backend
from StepDaddyLiveHD.components import navbar, card
from StepDaddyLiveHD.step_daddy import Channel


class State(rx.State):
    channels: List[Channel] = []
    search_query: str = ""
    now_playing_map: dict[str, dict] = {}

    @rx.var
    def filtered_channels(self) -> List[Channel]:
        if not self.search_query:
            return self.channels
        return [ch for ch in self.channels if self.search_query.lower() in ch.name.lower()]

    async def on_load(self):
        self.channels = backend.get_channels()
        # Recupera la mappa di cosa c'è in onda ora
        self.now_playing_map = backend.get_now_playing_map()


@rx.page("/", on_load=State.on_load)
def index() -> rx.Component:
    return rx.box(
        navbar(
            rx.box(
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
            ),
        ),
        rx.center(
            rx.cond(
                State.channels,
                rx.grid(
                    rx.foreach(
                        State.filtered_channels,
                        lambda channel: card(channel, State.now_playing_map.get(channel.id, None)),
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
app.register_lifespan_task(backend.update_epg)
