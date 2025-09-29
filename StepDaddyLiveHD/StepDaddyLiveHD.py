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


# ✅ Reflex still registers this page (but with a simple placeholder)
@rx.page(route="/stream/[id]", title="HiddnTV")
def stream_page(id: str = ""):
    return rx.center(
        rx.text(f"Loading stream {id}..."),
        height="100vh",
    )


# ✅ FastAPI backend route serves the real .m3u8
from fastapi.responses import PlainTextResponse
from StepDaddyLiveHD.step_daddy import StepDaddy
import asyncio

@backend.fastapi_app.get("/api/stream/{id}")
async def get_stream(id: str):
    step_daddy = StepDaddy()
    m3u8_data = await asyncio.to_thread(step_daddy.stream, id)
    return PlainTextResponse(m3u8_data, media_type="application/vnd.apple.mpegurl")


# ✅ Proper Reflex 0.8.7 mounting
def mount_backend(api):
    # Mount your backend FastAPI app into Reflex app
    api.mount("/", backend.fastapi_app)
    return api

# ✅ App definition
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="red",
    ),
    api_transformer=mount_backend,   # <-- correct for Reflex 0.8.7
)

# Background update task
app.register_lifespan_task(backend.update_channels)
