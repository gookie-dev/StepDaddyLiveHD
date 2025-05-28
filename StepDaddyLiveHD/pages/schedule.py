import reflex as rx
from typing import Dict, List, TypedDict
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from dateutil import parser
from StepDaddyLiveHD import backend
from StepDaddyLiveHD.components import navbar


class CanalItem(TypedDict):
    nombre: str
    id: str


class EventoItem(TypedDict):
    nombre: str
    hora: str
    dt: datetime
    categoria: str
    canales: List[CanalItem]


class EstadoHorario(rx.State):
    eventos: List[EventoItem] = []
    categorias: Dict[str, bool] = {}
    mostrar_solo_futuros: bool = True
    consulta: str = ""

    @staticmethod
    def obtener_canales(canales: dict) -> List[CanalItem]:
        lista_canales = []
        if isinstance(canales, list):
            for canal in canales:
                try:
                    lista_canales.append(CanalItem(nombre=canal["channel_name"], id=canal["channel_id"]))
                except:
                    continue
        elif isinstance(canales, dict):
            for clave in canales:
                try:
                    lista_canales.append(CanalItem(
                        nombre=canales[clave]["channel_name"], 
                        id=canales[clave]["channel_id"]
                    ))
                except:
                    continue
        return lista_canales

    def alternar_categoria(self, categoria):
        self.categorias[categoria] = not self.categorias.get(categoria, False)

    def doble_categoria(self, categoria):
        for cat in self.categorias:
            self.categorias[cat] = (cat == categoria)

    async def on_load(self):
        self.eventos = []
        categorias = {}
        dias = await backend.get_schedule()
        for dia in dias:
            nombre_dia = dia.split(" - ")[0]
            dt = parser.parse(nombre_dia, dayfirst=True)
            for categoria in dias[dia]:
                categorias[categoria] = True
                for evento in dias[dia][categoria]:
                    hora = evento["time"]
                    hora_int, minuto_int = map(int, hora.split(":"))
                    evento_dt = dt.replace(hour=hora_int, minute=minuto_int).replace(tzinfo=ZoneInfo("UTC"))
                    canales = self.obtener_canales(evento.get("channels"))
                    canales.extend(self.obtener_canales(evento.get("channels2")))
                    canales.sort(key=lambda c: c["nombre"])
                    self.eventos.append(EventoItem(
                        nombre=evento["event"],
                        hora=hora,
                        dt=evento_dt,
                        categoria=categoria,
                        canales=canales
                    ))
        self.categorias = dict(sorted(categorias.items()))
        self.eventos.sort(key=lambda e: e["dt"])

    @rx.event
    def set_mostrar_solo_futuros(self, valor: bool):
        self.mostrar_solo_futuros = valor

    @rx.event
    def set_consulta(self, valor: str):
        self.consulta = valor

    @rx.var
    def eventos_filtrados(self) -> List[EventoItem]:
        ahora = datetime.now(ZoneInfo("UTC")) - timedelta(minutes=30)
        texto = self.consulta.strip().lower()

        return [
            evento for evento in self.eventos
            if self.categorias.get(evento["categoria"], False)
               and (not self.mostrar_solo_futuros or evento["dt"] > ahora)
               and (texto == "" or texto in evento["nombre"].lower())
        ]


def tarjeta_evento(evento: EventoItem) -> rx.Component:
    return rx.card(
        rx.heading(evento["nombre"]),
        rx.hstack(
            rx.moment(evento["dt"], format="HH:mm", local=True),
            rx.moment(evento["dt"], format="ddd MMM DD YYYY", local=True),
            rx.badge(evento["categoria"], margin_top="0.2rem"),
        ),
        rx.hstack(
            rx.foreach(
                evento["canales"],
                lambda canal: rx.button(
                    canal["nombre"],
                    variant="surface",
                    color_scheme="gray",
                    size="1",
                    on_click=rx.redirect(f"/watch/{canal['id']}")
                ),
            ),
            wrap="wrap",
            margin_top="0.5rem",
        ),
        width="100%",
    )


def insignia_categoria(categoria) -> rx.Component:
    return rx.badge(
        categoria[0],
        color_scheme=rx.cond(
            categoria[1],
            "red",
            "gray",
        ),
        _hover={"color": "white"},
        style={"cursor": "pointer"},
        on_click=lambda: EstadoHorario.alternar_categoria(categoria[0]),
        on_double_click=lambda: EstadoHorario.doble_categoria(categoria[0]),
        size="2",
    )


@rx.page("/schedule", on_load=EstadoHorario.on_load)
def horario() -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.center(
                rx.vstack(
                    rx.cond(
                        EstadoHorario.categorias,
                        rx.card(
                            rx.input(
                                placeholder="Buscar eventos...",
                                on_change=EstadoHorario.set_consulta,
                                value=EstadoHorario.consulta,
                                width="100%",
                                size="3",
                            ),
                            rx.hstack(
                                rx.text("Filtrar por etiqueta:"),
                                rx.foreach(EstadoHorario.categorias, insignia_categoria),
                                spacing="2",
                                wrap="wrap",
                                margin_top="0.7rem",
                            ),
                            rx.hstack(
                                rx.text("Ocultar eventos pasados"),
                                rx.switch(
                                    on_change=EstadoHorario.set_mostrar_solo_futuros,
                                    checked=EstadoHorario.mostrar_solo_futuros,
                                    margin_top="0.2rem"
                                ),
                                margin_top="0.5rem",
                            ),
                        ),
                        rx.spinner(size="3"),
                    ),
                    rx.foreach(EstadoHorario.eventos_filtrados, tarjeta_evento),
                ),
            ),
            padding_top="10rem",
        ),
    )
