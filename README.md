# Daddy Live Proxy 🚀

This is a self-hosted IPTV proxy built with [Reflex](https://reflex.dev), enabling you to watch over 1,000 📺 TV channels and search for live events or sports matches ⚽🏀. Stream directly in your browser 🌐 or through any media player client 🎶. You can also download the entire playlist (`playlist.m3u8`) and guide (`guide.xml`) and integrate it with platforms like Jellyfin 🍇 or other IPTV media players.

## ✨ Features

- **📱 Stream Anywhere**: Watch TV channels on any device via the web or media players.
- **🔎 Event Search**: Quickly find the right channel for live events or sports.
- **📄 Playlist M3U8**: Download the `playlist.m3u8` and use it with Jellyfin or any IPTV client.
- **🗓️ Guide XMLTV**: Access scheduling information at `guide.xml` for use with media servers like Jellyfin.
- **✅ Channel Filtering**: Select which channels appear in the playlist and generated guide.
- **🕒 Daily Guide Updates**: Automatically refresh `guide.xml` once per day at a user-defined time.
- **⚙️ Docker-First Hosting**: Run the application using Docker or Docker Compose with flexible configuration options.

## 🐳 Docker Installation (Required)

> ⚠️ **Important:** When exposing the application on your local network (LAN), set `API_URL` in your `.env` file to the **Local IP address** of the server hosting the container.

To run with Docker Compose:

1. Install Docker and Docker Compose.

2. Clone the repository and change into the project directory.

3. Start the application with Docker Compose:

   ```bash
   docker compose up -d
   ```

To run with plain Docker:

1. Build the Docker container:

   ```bash
   docker build -t daddyliveproxy .
   ```

2. Run the container w:
   ```bash
   docker run -p 3000:3000 daddyliveproxy
   ```

## ⚙️ Configuration

### Environment Variables

- **PORT**: Set a custom port for the server.
- **API_URL**: Set the domain or IP where the server is reachable.
- **SOCKS5**: Proxy DLHD traffic through a SOCKS5 server if needed.
- **PROXY_CONTENT**: Proxy video content itself through your server (optional).
- **TZ**: Timezone used for schedules and guide generation (e.g., `UTC`, `Europe/Rome`).
- **GUIDE_UPDATE**: Daily time (`HH:MM`) to refresh `guide.xml` (e.g., `03:00`).

Edit the `.env` for docker compose.

### Example Docker Command

```bash
docker build --build-arg PROXY_CONTENT=TRUE --build-arg API_URL=https://example.com --build-arg SOCKS5=user:password@proxy.example.com:1080 --build-arg TZ=UTC --build-arg GUIDE_UPDATE=03:00 -t daddyliveproxy .
docker run --restart unless-stopped -e PROXY_CONTENT=TRUE -e API_URL=https://example.com -e SOCKS5=user:password@proxy.example.com:1080 -e TZ=UTC -e GUIDE_UPDATE=03:00 -p 3000:3000 daddyliveproxy
```

## 🗺️ Site Map

### Pages Overview:

- **🏠 Home**: Browse and search for TV channels.
- **📅 Schedule**: Quickly find channels broadcasting live events and sports.
- **📺 Channels**: View the full list of available channels.
- **⚙️ Settings**: Configure channel visibility and other preferences.
- **📄 Playlist Download**: Download the `playlist.m3u8` file for integration with media players.
- **🗓️ Guide Download**: Download the `guide.xml` file for use with media servers.

## 📚 Hosting Options

Check out the [official Reflex hosting documentation](https://reflex.dev/docs/hosting/self-hosting/) for more advanced self-hosting setups!
