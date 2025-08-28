import reflex as rx
import StepDaddyLiveHD.pages
from typing import List
from StepDaddyLiveHD import backend
from StepDaddyLiveHD.components import navbar, card
from StepDaddyLiveHD.step_daddy import Channel


class State(rx.State):
    channels: List[Channel] = []
    search_query: str = ""

    @rx.var
    def filtered_channels(self) -> List[Channel]:
        if not self.search_query:
            return self.channels
        return [ch for ch in self.channels if self.search_query.lower() in ch.name.lower()]

    async def on_load(self):
        self.channels = backend.get_channels()


# ✅ Home page
@rx.page("/", on_load=State.on_load, title="HiddnTV")
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


# ✅ Stream endpoint (Reflex-safe)
# Uses /stream/[id] instead of /stream/[id].m3u8
@rx.page(route="/stream/[id]", title="HiddnTV")
def stream_page(id: str):
    from StepDaddyLiveHD.step_daddy import StepDaddy
    import asyncio

    step_daddy = StepDaddy()
    m3u8_data = asyncio.run(step_daddy.stream(id))

    # Serve .m3u8 data with correct headers so player knows it’s an HLS playlist
    return rx.Response(
        content=m3u8_data,
        headers={"Content-Type": "application/vnd.apple.mpegurl"}
    )


# ✅ App definition
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="red",
    ),
    api_transformer=backend.fastapi_app,
)

app.register_lifespan_task(backend.update_channels)
