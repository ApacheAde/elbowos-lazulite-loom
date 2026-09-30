#!/usr/bin/env python3
"""Lazulite Loom — neon weft-shuttle arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/LAZULITE_LOOM_ElbowOS.mp4")
TITLE, HANDLE = "LAZULITE LOOM", "x.com/ElbowOS"

INK = (5, 10, 28)
NAVY = (10, 22, 58)
AZURE = (48, 140, 255)
CYAN = (80, 240, 255)
GOLD = (255, 204, 72)
ROSE = (255, 78, 148)
MINT = (96, 255, 186)
LILAC = (198, 176, 255)
WHITE = (248, 250, 255)
FOG = (188, 210, 255)
MAG = (220, 70, 255)

PAL = (CYAN, GOLD, ROSE, MINT, MAG)
LEFT, RIGHT = 120, W - 120
NEEDLE_Y = 1420
WARPS = 7


class Shuttle:
    __slots__ = ("x", "y", "vx", "col", "r", "alive")

    def __init__(self, y=None):
        self.col = random.choice(PAL)
        self.r = random.randint(16, 22)
        self.y = y if y is not None else random.uniform(280, 1180)
        left = random.random() < 0.5
        self.x = -40 if left else W + 40
        self.vx = (1 if left else -1) * random.uniform(280, 520)
        self.alive = True


class Game:
    def __init__(self, record=False):
        self.record = record
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY and not record else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            self.screen = pygame.Surface((W, H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("dejavusans", 50, bold=True)
        self.font_md = pygame.font.SysFont("dejavusans", 34, bold=True)
        self.font_sm = pygame.font.SysFont("dejavusans", 26)
        self.reset()

    def reset(self):
        self.score = 0
        self.t = 0.0
        self.x = W / 2
        self.vx = 0.0
        self.streak = 0
        self.flash = 0.0
        self.shuttles = []
        self.sparks = []
        self.cloth = []  # list of (col, phase)
        self.motes = [{"x": random.uniform(0, W), "y": random.uniform(0, H),
                       "s": random.uniform(1.0, 2.8), "v": random.uniform(12, 40)}
                      for _ in range(55)]
        self.spawn_cd = 0.0
        for i in range(5):
            s = Shuttle(y=360 + i * 150)
            s.x = random.uniform(160, W - 160)
            self.shuttles.append(s)

    def burst(self, x, y, col, n=16):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            sp = random.uniform(90, 380)
            self.sparks.append({"x": x, "y": y, "vx": math.cos(a) * sp,
                                "vy": math.sin(a) * sp, "life": random.uniform(0.2, 0.65),
                                "col": col})

    def autoplay(self):
        living = [s for s in self.shuttles if s.alive]
        if not living:
            self.vx *= 0.8
            return
        def eta(s):
            if s.vx == 0:
                return 99
            return abs(s.x - self.x) / (abs(s.vx) + 1) + abs(s.y - NEEDLE_Y) * 0.002
        tgt = min(living, key=eta)
        err = tgt.x - self.x
        self.vx = max(-640, min(640, err * 5.4 + tgt.vx * 0.35))

    def handle(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
            self.reset()

    def update(self, dt):
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        if self.record:
            self.autoplay()
        else:
            keys = pygame.key.get_pressed()
            ax = 0.0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                ax -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                ax += 1
            self.vx += ax * 2100 * dt
            self.vx *= 0.84
        self.x = max(LEFT + 28, min(RIGHT - 28, self.x + self.vx * dt))
        self.spawn_cd -= dt
        if self.spawn_cd <= 0 and len(self.shuttles) < 8:
            self.shuttles.append(Shuttle())
            self.spawn_cd = random.uniform(0.35, 0.75)
        for s in self.shuttles:
            s.x += s.vx * dt
            s.y += math.sin(self.t * 3.2 + s.x * 0.01) * 18 * dt
            if s.alive and abs(s.y - NEEDLE_Y) < 38 and abs(s.x - self.x) < 46:
                s.alive = False
                self.streak += 1
                self.score += 40 + self.streak * 8
                self.cloth.append((s.col, self.t))
                if len(self.cloth) > 18:
                    self.cloth.pop(0)
                self.burst(s.x, s.y, s.col, 18)
        keep = []
        for s in self.shuttles:
            off = s.x < -80 or s.x > W + 80
            if off and s.alive:
                self.streak = 0
                self.flash = 0.22
                self.score = max(0, self.score - 12)
            if not off:
                keep.append(s)
        self.shuttles = keep
        for m in self.motes:
            m["y"] += m["v"] * dt
            if m["y"] > H + 6:
                m["y"] = -6
                m["x"] = random.uniform(0, W)
        for sp in self.sparks:
            sp["x"] += sp["vx"] * dt
            sp["y"] += sp["vy"] * dt
            sp["life"] -= dt
        self.sparks = [sp for sp in self.sparks if sp["life"] > 0]

    def draw(self, s):
        s.fill(INK)
        pulse = 0.5 + 0.5 * math.sin(self.t * 2.4)
        for m in self.motes:
            pygame.draw.circle(s, NAVY, (int(m["x"]), int(m["y"])), int(m["s"]))
        pygame.draw.rect(s, NAVY, (0, 0, LEFT - 20, H))
        pygame.draw.rect(s, NAVY, (RIGHT + 20, 0, W - RIGHT - 20, H))
        pygame.draw.line(s, AZURE, (LEFT - 20, 0), (LEFT - 20, H), 6)
        pygame.draw.line(s, AZURE, (RIGHT + 20, 0), (RIGHT + 20, H), 6)
        pygame.draw.line(s, GOLD, (LEFT - 10, 0), (LEFT - 10, H), 2)
        pygame.draw.line(s, GOLD, (RIGHT + 10, 0), (RIGHT + 10, H), 2)
        gap = (RIGHT - LEFT) / (WARPS - 1)
        for i in range(WARPS):
            wx = LEFT + i * gap
            wob = int(math.sin(self.t * 2.6 + i) * 6)
            col = CYAN if i % 2 == 0 else LILAC
            pygame.draw.line(s, col, (int(wx + wob), 230), (int(wx - wob * 0.4), H - 90), 3)
        cloth_top = 210
        for i, (col, ph) in enumerate(self.cloth):
            y = cloth_top + i * 16
            pygame.draw.rect(s, col, (LEFT, y, RIGHT - LEFT, 14), border_radius=4)
            pygame.draw.rect(s, WHITE, (LEFT + 8, y + 4, RIGHT - LEFT - 16, 4))
        pygame.draw.rect(s, AZURE, (LEFT - 8, NEEDLE_Y - 8, RIGHT - LEFT + 16, 16), border_radius=8)
        pygame.draw.rect(s, GOLD, (LEFT, NEEDLE_Y - 3, RIGHT - LEFT, 6), border_radius=4)
        for sh in self.shuttles:
            if not sh.alive:
                continue
            cx, cy = int(sh.x), int(sh.y)
            pygame.draw.ellipse(s, sh.col, (cx - 34, cy - sh.r, 68, sh.r * 2))
            pygame.draw.ellipse(s, WHITE, (cx - 14, cy - 8, 18, 14))
            pygame.draw.circle(s, INK, (cx + 18, cy), 5)
            tx = cx - int(math.copysign(50, sh.vx))
            pygame.draw.line(s, sh.col, (cx, cy), (tx, cy + int(math.sin(self.t * 10) * 8)), 3)
        nx, ny = int(self.x), NEEDLE_Y
        glow = ROSE if self.flash > 0 else GOLD
        pygame.draw.polygon(s, glow, [(nx, ny - 54), (nx + 22, ny + 8), (nx - 22, ny + 8)])
        pygame.draw.circle(s, WHITE, (nx, ny - 10), 16)
        pygame.draw.circle(s, CYAN, (nx, ny - 10), 8)
        pygame.draw.rect(s, LILAC, (nx - 6, ny + 8, 12, 48), border_radius=5)
        for sp in self.sparks:
            pygame.draw.circle(s, sp["col"], (int(sp["x"]), int(sp["y"])), max(2, int(sp["life"] * 11)))
        if self.flash > 0:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 50, 110, int(80 * self.flash / 0.22)))
            s.blit(veil, (0, 0))
        title = self.font_lg.render(TITLE, True, LILAC)
        s.blit(title, title.get_rect(center=(W // 2, 58)))
        handle = self.font_sm.render(HANDLE, True, CYAN)
        s.blit(handle, handle.get_rect(center=(W // 2, 110)))
        meta = self.font_md.render(f"SCORE  {self.score}    STREAK  {self.streak}    PICKS  {len(self.cloth)}", True, FOG)
        s.blit(meta, meta.get_rect(center=(W // 2, 168)))
        hint = self.font_sm.render("A / D  slide the beater    R  reset", True, GOLD)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 48)))
        rim = int(10 + 5 * pulse)
        pygame.draw.rect(s, AZURE, (16, 16, W - 32, H - 32), rim, border_radius=26)

    def play(self):
        run = True
        while run:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    run = False
                self.handle(ev)
            self.update(dt)
            self.draw(self.screen)
            pygame.display.flip()
        pygame.quit()

    def record_mp4(self, path):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = SECS * FPS
        surf = self.screen
        for _ in range(frames):
            self.update(1.0 / FPS)
            self.draw(surf)
            proc.stdin.write(pygame.image.tostring(surf, "RGB"))
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", path)
        pygame.quit()


def main():
    g = Game(record=RECORD)
    if PLAY and not RECORD:
        g.play()
    else:
        g.record_mp4(OUT)


if __name__ == "__main__":
    main()
