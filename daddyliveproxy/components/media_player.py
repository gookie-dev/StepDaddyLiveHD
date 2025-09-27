import reflex as rx
from reflex.components.component import NoSSRComponent


class MediaPlayer(NoSSRComponent):
    library = "/public/player"
    lib_dependencies: list[str] = ["@vidstack/react@next"]
    tag = "Player"
    title: rx.Var[str]
    src: rx.Var[str]
    autoplay: bool = True
