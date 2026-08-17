"""Music & media control — playback, mood-based recommendations.

ANUBIS controls music playback to:
- Play music based on mood/activity
- Control volume and playback
- Suggest music for activities (work, exercise, relax, sleep)
- Integrate with local music, Spotify, or other services

CONTROLLERS:
- MPD (Music Player Daemon) — local music, standard protocol
- VLC HTTP interface — local playback
- Spotify Web API (requires OAuth)
- PulseAudio/PipeWire — system volume control

Uses stdlib only for MPD and VLC. Spotify requires spotipy library.
"""
from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# Playback states
PLAYBACK_PLAYING = "playing"
PLAYBACK_PAUSED = "paused"
PLAYBACK_STOPPED = "stopped"

# Mood/activity presets
MOOD_CALM = "calm"
MOOD_ENERGETIC = "energetic"
MOOD_FOCUS = "focus"
MOOD_HAPPY = "happy"
MOOD_SAD = "sad"
MOOD_STRESSED = "stressed"
MOOD_EXERCISE = "exercise"
MOOD_SLEEP = "sleep"
MOOD_PARTY = "party"

# Controllers
CTRL_MPD = "mpd"
CTRL_VLC = "vlc"
CTRL_SPOTIFY = "spotify"
CTRL_SYSTEM = "system"


@dataclass
class Track:
    """A music track."""
    track_id: str = ""
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float = 0.0
    url: str = ""
    source: str = ""  # "local", "spotify", etc.

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration,
            "source": self.source,
        }


@dataclass
class Playlist:
    """A playlist."""
    playlist_id: str
    name: str = ""
    tracks: list[Track] = field(default_factory=list)
    mood: str = ""
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "playlist_id": self.playlist_id,
            "name": self.name,
            "tracks": [t.to_dict() for t in self.tracks],
            "mood": self.mood,
            "track_count": len(self.tracks),
        }


class MusicController:
    """Music and media control system.

    Controls playback via MPD, VLC, or Spotify. Provides mood-based
    recommendations and system volume control.
    """

    ACTOR = "anubis.music"

    MOOD_PRESETS: dict[str, dict[str, Any]] = {
        MOOD_CALM: {"tempo": "slow", "genre": ["ambient", "classical", "jazz"], "volume": 40},
        MOOD_ENERGETIC: {"tempo": "fast", "genre": ["rock", "electronic", "pop"], "volume": 70},
        MOOD_FOCUS: {"tempo": "medium", "genre": ["classical", "ambient", "lo-fi"], "volume": 30},
        MOOD_HAPPY: {"tempo": "upbeat", "genre": ["pop", "funk", "soul"], "volume": 60},
        MOOD_SAD: {"tempo": "slow", "genre": ["blues", "indie", "acoustic"], "volume": 35},
        MOOD_STRESSED: {"tempo": "slow", "genre": ["ambient", "nature", "classical"], "volume": 30},
        MOOD_EXERCISE: {"tempo": "fast", "genre": ["electronic", "hip-hop", "rock"], "volume": 80},
        MOOD_SLEEP: {"tempo": "very slow", "genre": ["ambient", "white noise", "nature"], "volume": 20},
        MOOD_PARTY: {"tempo": "upbeat", "genre": ["dance", "pop", "hip-hop"], "volume": 75},
    }

    def __init__(
        self,
        root: str | Path,
        *,
        mpd_host: str = "localhost",
        mpd_port: int = 6600,
        vlc_host: str = "localhost",
        vlc_port: int = 8080,
        vlc_password: str = "",
        ledger: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.mpd_host = mpd_host
        self.mpd_port = mpd_port
        self.vlc_host = vlc_host
        self.vlc_port = vlc_port
        self.vlc_password = vlc_password
        self.ledger = ledger

        self._state_dir = self.root / "memory" / "music"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._playlists_file = self._state_dir / "playlists.json"

        self._playlists: dict[str, Playlist] = {}
        self._current_track: Track | None = None
        self._playback_state = PLAYBACK_STOPPED
        self._volume = 50
        self._current_mood = ""
        self._load()

    # --------------------------------------------------- playback control

    def play(self, track_id: str = "") -> dict[str, Any]:
        """Start or resume playback."""
        # Try MPD
        if self._mpd_command(f"play {track_id}" if track_id else "play"):
            self._playback_state = PLAYBACK_PLAYING
            return {"success": True, "controller": CTRL_MPD}
        # Try VLC
        if self._vlc_command("pl_play"):
            self._playback_state = PLAYBACK_PLAYING
            return {"success": True, "controller": CTRL_VLC}
        return {"success": False, "error": "No music controller available"}

    def pause(self) -> dict[str, Any]:
        if self._mpd_command("pause"):
            self._playback_state = PLAYBACK_PAUSED
            return {"success": True}
        if self._vlc_command("pl_pause"):
            self._playback_state = PLAYBACK_PAUSED
            return {"success": True}
        return {"success": False}

    def stop(self) -> dict[str, Any]:
        if self._mpd_command("stop"):
            self._playback_state = PLAYBACK_STOPPED
            return {"success": True}
        if self._vlc_command("pl_stop"):
            self._playback_state = PLAYBACK_STOPPED
            return {"success": True}
        return {"success": False}

    def next(self) -> dict[str, Any]:
        if self._mpd_command("next"):
            return {"success": True}
        if self._vlc_command("pl_next"):
            return {"success": True}
        return {"success": False}

    def previous(self) -> dict[str, Any]:
        if self._mpd_command("previous"):
            return {"success": True}
        if self._vlc_command("pl_previous"):
            return {"success": True}
        return {"success": False}

    def set_volume(self, volume: int) -> dict[str, Any]:
        if not 0 <= volume <= 100:
            return {"success": False, "error": "Volume must be 0-100"}
        if self._mpd_command(f"setvol {volume}"):
            self._volume = volume
            return {"success": True}
        # Try system volume
        if self._set_system_volume(volume):
            self._volume = volume
            return {"success": True}
        self._volume = volume  # store even if no controller
        return {"success": False}

    def get_volume(self) -> int:
        return self._volume

    # --------------------------------------------------- mood-based

    def set_mood(self, mood: str) -> dict[str, Any]:
        """Set playback based on mood."""
        preset = self.MOOD_PRESETS.get(mood)
        if preset is None:
            return {"success": False, "error": f"Unknown mood: {mood}"}

        self._current_mood = mood
        self.set_volume(preset["volume"])

        # Find matching playlist
        for playlist in self._playlists.values():
            if playlist.mood == mood:
                self._log("mood.set", {"mood": mood, "playlist": playlist.name})
                return {"success": True, "mood": mood, "playlist": playlist.to_dict()}

        return {"success": True, "mood": mood, "volume": preset["volume"]}

    def get_mood_recommendation(self, emotion: str) -> str:
        """Map an emotion to a music mood."""
        mapping = {
            "happy": MOOD_HAPPY, "sad": MOOD_SAD, "angry": MOOD_ENERGETIC,
            "stressed": MOOD_STRESSED, "calm": MOOD_CALM, "fearful": MOOD_CALM,
            "neutral": MOOD_FOCUS, "tired": MOOD_SLEEP,
        }
        return mapping.get(emotion.lower(), MOOD_FOCUS)

    # --------------------------------------------------- playlists

    def create_playlist(self, name: str, mood: str = "") -> Playlist:
        playlist_id = hashlib.sha256(
            f"playlist:{name}:{time.time()}".encode()
        ).hexdigest()[:16]
        playlist = Playlist(
            playlist_id=playlist_id, name=name, mood=mood,
            created_at=time.time(),
        )
        self._playlists[playlist_id] = playlist
        self._save()
        return playlist

    def add_track_to_playlist(
        self, playlist_id: str, title: str, artist: str = "",
        album: str = "", duration: float = 0, url: str = "",
    ) -> bool:
        playlist = self._playlists.get(playlist_id)
        if playlist is None:
            return False
        track = Track(
            track_id=hashlib.sha256(
                f"track:{title}:{artist}:{time.time()}".encode()
            ).hexdigest()[:16],
            title=title, artist=artist, album=album,
            duration=duration, url=url,
        )
        playlist.tracks.append(track)
        self._save()
        return True

    def get_playlists(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self._playlists.values()]

    def get_playlist(self, playlist_id: str) -> dict[str, Any] | None:
        p = self._playlists.get(playlist_id)
        return p.to_dict() if p else None

    # --------------------------------------------------- controllers

    def _mpd_command(self, command: str) -> bool:
        """Send a command to MPD."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.mpd_host, self.mpd_port))
            sock.recv(1024)  # welcome message
            sock.send(f"{command}\n".encode())
            response = sock.recv(1024).decode()
            sock.close()
            return "OK" in response or "ACK" not in response
        except Exception:
            return False

    def _vlc_command(self, command: str) -> bool:
        """Send a command to VLC HTTP interface."""
        try:
            url = f"http://{self.vlc_host}:{self.vlc_port}/requests/status.xml?command={command}"
            req = urllib.request.Request(url)
            if self.vlc_password:
                import base64
                auth = base64.b64encode(f":{self.vlc_password}".encode()).decode()
                req.add_header("Authorization", f"Basic {auth}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _set_system_volume(self, volume: int) -> bool:
        """Set system volume via amixer (Linux) or equivalent."""
        try:
            # Linux: amixer
            result = subprocess.run(
                ["amixer", "set", "Master", f"{volume}%"],
                capture_output=True, timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    # --------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        return {
            "playback_state": self._playback_state,
            "volume": self._volume,
            "current_mood": self._current_mood,
            "playlists": len(self._playlists),
            "mpd_available": self._mpd_command("status"),
            "current_track": self._current_track.to_dict() if self._current_track else None,
        }

    # --------------------------------------------------- persistence

    def _load(self) -> None:
        if not self._playlists_file.exists():
            return
        try:
            data = json.loads(self._playlists_file.read_text(encoding="utf-8"))
            for p_id, p in data.items():
                playlist = Playlist(
                    playlist_id=p_id, name=p.get("name", ""),
                    mood=p.get("mood", ""), created_at=p.get("created_at", 0),
                )
                for t in p.get("tracks", []):
                    playlist.tracks.append(Track(
                        track_id=t.get("track_id", ""),
                        title=t.get("title", ""),
                        artist=t.get("artist", ""),
                        album=t.get("album", ""),
                        duration=t.get("duration", 0),
                        url=t.get("url", ""),
                    ))
                self._playlists[p_id] = playlist
        except Exception:
            pass

    def _save(self) -> None:
        data = {p_id: p.to_dict() for p_id, p in self._playlists.items()}
        self._playlists_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
