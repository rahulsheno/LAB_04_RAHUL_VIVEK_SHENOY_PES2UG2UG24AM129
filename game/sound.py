"""Sound effects, synthesized at runtime (no audio files or extra dependencies).

If no audio device is available the game keeps running silently.
"""
import array
import math
import random

import pygame

SAMPLE_RATE = 22050


def _make_sound(segments, volume=0.4, noise=False):
    """Build a Sound from (start_hz, end_hz, seconds) segments (a frequency sweep each)."""
    samples = array.array("h")
    for start_hz, end_hz, seconds in segments:
        n = int(SAMPLE_RATE * seconds)
        phase = 0.0
        for i in range(n):
            t = i / n
            freq = start_hz + (end_hz - start_hz) * t
            phase += 2 * math.pi * freq / SAMPLE_RATE
            wave = math.copysign(1.0, math.sin(phase))      # square wave: retro feel
            if noise:
                wave = 0.6 * wave + 0.4 * random.uniform(-1, 1)
            envelope = 1.0 - t                               # fade out to avoid clicks
            samples.append(int(32767 * volume * envelope * wave))
    return pygame.mixer.Sound(buffer=samples.tobytes())


class SoundManager:
    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            self.sounds = {
                "shoot": _make_sound([(900, 300, 0.12)], volume=0.25),
                "explosion": _make_sound([(260, 40, 0.30)], volume=0.5, noise=True),
                "game_over": _make_sound([(440, 330, 0.25), (330, 220, 0.25), (220, 110, 0.5)], volume=0.4),
            }
            self.enabled = True
        except pygame.error as err:
            print(f"Sound disabled: {err}")

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()
