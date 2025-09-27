import { Captions, MediaPlayer, MediaProvider, Poster } from "@vidstack/react";
import {
  DefaultVideoLayout,
  defaultLayoutIcons,
} from "@vidstack/react/player/layouts/default";
import "@vidstack/react/player/styles/default/layouts/audio.css";
import "@vidstack/react/player/styles/default/layouts/video.css";
import "@vidstack/react/player/styles/default/theme.css";

function InjectCSS() {
  const css = `
    .media-player[data-view-type="video"] {
      aspect-ratio: 16 / 9;
    }

    .vds-video-layout {
      --video-brand: hsl(0, 0%, 96%);
    }

    .vds-audio-layout {
      --audio-brand: hsl(0, 0%, 96%);
    }

    .plyr {
      --plyr-color-main: hsl(198, 100%, 50%);
    }
    
    .vds-slider-chapters {
      display: none;
    }
    
    .rt-Container {
      align-self: center;
    }
  `;

  return <style dangerouslySetInnerHTML={{ __html: css }} />;
}

export function Player({ title, src }) {
  return (
    <>
      <InjectCSS />
      <MediaPlayer
        title={title}
        src={src}
        viewType="video"
        streamType="live"
        logLevel="warn"
        playsInline
        autoplay
        muted
      >
        <MediaProvider>
          <Poster className="vds-poster" />
        </MediaProvider>
        <DefaultVideoLayout icons={defaultLayoutIcons} />
        <Captions className="vds-captions" />
      </MediaPlayer>
    </>
  );
}
