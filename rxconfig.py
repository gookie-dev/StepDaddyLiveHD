import reflex as rx
import os

proxy_content = os.environ.get("PROXY_CONTENT", "TRUE").upper() == "TRUE"
socks5 = os.environ.get("SOCKS5", "")

print(f"PROXY_CONTENT: {proxy_content}\nSOCKS5: {socks5}")

config = rx.Config(
    app_name="StepDaddyLiveHD",   # must match folder/module name
    proxy_content=proxy_content,
    socks5=socks5,
    show_built_with_reflex=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
