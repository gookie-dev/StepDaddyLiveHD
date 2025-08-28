# StepDaddyLiveHD 🚀

A self-hosted IPTV proxy built with [Reflex](https://reflex.dev), enabling you to watch over 1,000 📺 TV channels and search for live events or sports matches ⚽🏀. Stream directly in your browser 🌐 or through any media player client 🎶. You can also download the entire playlist (`playlist.m3u8`) and integrate it with platforms like Jellyfin 🍇 or other IPTV media players.

---

## ✨ Features

- **📱 Stream Anywhere**: Watch TV channels on any device via the web or media players.
- **🔎 Event Search**: Quickly find the right channel for live events or sports.
- **📄 Playlist Integration**: Download the `playlist.m3u8` and use it with Jellyfin or any IPTV client.
- **⚙️ Customizable Hosting**: Host the application locally or deploy it via Docker with various configuration options.

---

## 🐳 Docker Installation (Recommended)

> ⚠️ **Important:** If you plan to use this application across your local network (LAN), you must set `API_URL` to the **local IP address** of the device hosting the server in `.env`.

1. Make sure you have Docker and Docker Compose installed on your system.
2. Clone the repository and navigate into the project directory:
3. Run the following command to start the application:
   ```bash
   docker compose up -d
   ```

Plain Docker:
```bash
docker build -t step-daddy-live-hd .
docker run -p 3000:3000 step-daddy-live-hd
```

---

## 🖥️ Local Installation

1. Install Python 🐍 (tested with version 3.12).
2. Clone the repository and navigate into the project directory:
   ```bash
   git clone https://github.com/gookie-dev/StepDaddyLiveHD
   cd StepDaddyLiveHD
   ```
3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Initialize Reflex:
   ```bash
   reflex init
   ```
6. Run the application in production mode:
   ```bash
   reflex run --env prod
   ```

---

## ⚙️ Configuration

### Environment Variables

- **PORT**: Set a custom port for the server.
- **API_URL**: Set the domain or IP where the server is reachable.
- **SOCKS5**: Proxy DLHD traffic through a SOCKS5 server if needed.
- **PROXY_CONTENT**: Proxy video content itself through your server (optional).

Edit the `.env` for docker compose.

### Example Docker Command
```bash
docker build --build-arg PROXY_CONTENT=FALSE --build-arg API_URL=https://example.com --build-arg SOCKS5=user:password@proxy.example.com:1080 -t step-daddy-live-hd .
docker run -e PROXY_CONTENT=FALSE -e API_URL=https://example.com -e SOCKS5=user:password@proxy.example.com:1080 -p 3000:3000 step-daddy-live-hd
```

---

## 🗺️ Site Map

### Pages Overview:

- **🏠 Home**: Browse and search for TV channels.
- **📺 Live Events**: Quickly find channels broadcasting live events and sports.
- **📥 Playlist Download**: Download the `playlist.m3u8` file for integration with media players.

---

## 📸 Screenshots

**Home Page**
<img alt="Home Page" src="https://files.catbox.moe/qlqqs5.png">

**Watch Page**
<img alt="Watch Page" src="https://files.catbox.moe/974r9w.png">

**Live Events**
<img alt="Live Events" src="https://files.catbox.moe/7oawie.png">

---

## 📚 Hosting Options

Check out the [official Reflex hosting documentation](https://reflex.dev/docs/hosting/self-hosting/) for more advanced self-hosting setups!
