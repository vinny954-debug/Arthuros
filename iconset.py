"""ArthurOS icon set: one registry, every icon unique.

Every icon the skin shows comes from REGISTRY (name -> 16x16 pixel grid).
A registry entry is either a base drawing or a base plus a 9x9 corner badge
(an "emblem"), so a family of related icons shares a picture but never a
pixel pattern: Movies, Recently added movies and Movie genres are the same
film strip with nothing, a star, and a tag in the corner.

DEFAULT_MAP says which registry icon each of Kodi's Default*.png fallbacks
uses. Two Kodi names may share one icon only if they mean the same thing to
the viewer, and then they must be listed in ALIASES with the reason.
iconcheck.py enforces all of this on every build.

Pixel keys are the ones mkmedia.KEY understands.
"""

# ------------------------------------------------------------------ drawing
def blank():
    return [["."] * 16 for _ in range(16)]

def rows_of(c):
    return ["".join(r) for r in c]

def rect(c, x0, y0, x1, y1, fill=None, outline="K"):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            edge = x in (x0, x1) or y in (y0, y1)
            if edge and outline:
                c[y][x] = outline
            elif fill and not edge:
                c[y][x] = fill

def paint(c, x, y, rows, skip="."):
    for dy, r in enumerate(rows):
        for dx, ch in enumerate(r):
            if ch != skip:
                c[y + dy][x + dx] = ch

def recolour(rows, a, b):
    tr = str.maketrans(a, b)
    return [r.translate(tr) for r in rows]

# ------------------------------------------------------------ new base art
BASES = {}

# VHS cassette: the Videos section (files and sources, not the library)
c = blank()
rect(c, 1, 3, 14, 12, fill="E")
rect(c, 3, 4, 12, 7, fill="W", outline="W")
for x in (4, 5, 10, 11):
    c[5][x] = c[6][x] = "K"
rect(c, 4, 9, 11, 12, fill="d")
BASES["video"] = rows_of(c)

# monitor with a play triangle: Player settings
c = blank()
rect(c, 1, 1, 14, 11, fill="h")
rect(c, 2, 2, 13, 10, fill="B", outline="h")
paint(c, 6, 3, ["W", "WW", "WWW", "WWWW", "WWW", "WW", "W"])
paint(c, 6, 12, ["KhhK"]); c[12][6] = c[12][9] = "K"
rect(c, 4, 13, 11, 14, fill=None)
BASES["player"] = rows_of(c)

# four books on a shelf: Media (library) settings
c = blank()
for (x0, top, col) in ((1, 2, "R"), (4, 4, "B"), (7, 3, "Y"), (10, 5, "G")):
    rect(c, x0, top, x0 + 3, 13, fill=col)
    c[top + 2][x0 + 1] = c[top + 2][x0 + 2] = "W"
rect(c, 0, 13, 15, 14, fill=None)
BASES["media"] = rows_of(c)

# an Arthur window: Interface settings
c = blank()
rect(c, 1, 2, 14, 13, fill="W")
rect(c, 1, 2, 14, 5, fill="R")
for x in (10, 12):
    c[3][x] = c[4][x] = "W"
for y in (7, 9, 11):
    for x in range(3, 12 if y != 11 else 9):
        c[y][x] = "g"
BASES["interface"] = rows_of(c)

# painter's palette and brush: Skin settings
BASES["skin"] = [
"................",
"....KKKKKK......",
"..KKwwwwwwKK....",
".KwwRRwwBBwwK...",
".KwwRRwwBBwwwK..",
"KwwwwwwwwwwwwK..",
"KwGGwwwwwwwwK...",
"KwGGwwwwwwKK....",
"KwwwwwwwwK....K.",
"KwwYYwwwwK...KoK",
".KwYYwwwwwK.KoK.",
"..KwwwwwwwwKoK..",
"...KKKKKKKKoK...",
"..........KEK...",
".........KEK....",
"..........K.....",
]

# radio mast with waves: Services (UPnP, web server, AirPlay...)
BASES["services"] = [
"................",
"..K..........K..",
".K..K......K..K.",
"K..K...KK...K..K",
"K..K..KRRK..K..K",
"K..K..KRRK..K..K",
".K..K..KK..K..K.",
"..K....KK....K..",
".......KK.......",
"......KhhK......",
"......KhhK......",
".....KhKKhK.....",
".....KhKKhK.....",
"....KhK..KhK....",
"...KKKK..KKKK...",
"................",
]

# a microchip: System settings
BASES["system"] = [
"................",
"....K.K.K.K.K...",
"....K.K.K.K.K...",
"..KKKKKKKKKKKK..",
"KKKEEEEEEEEEEKKK",
"..KEhhhhhhhhEK..",
"KKKEhEEEEEEhEKKK",
"..KEhEGGGGEhEK..",
"KKKEhEGGGGEhEKKK",
"..KEhEEEEEEhEK..",
"KKKEhhhhhhhhEKKK",
"..KEEEEEEEEEEK..",
"..KKKKKKKKKKKK..",
"....K.K.K.K.K...",
"....K.K.K.K.K...",
"................",
]

# joystick: Games
BASES["games"] = [
"................",
"......KKK.......",
".....KRRRK......",
".....KRRRK......",
"......KKK.......",
".......K........",
".......K........",
".......K........",
".KKKKKKKKKKKKKK.",
".KhhhhhhhhhhhhK.",
".KhRRhhhhhhhhhK.",
".KhRRhhhhhhhhhK.",
".KhhhhhhhhhhhhK.",
".KEEEEEEEEEEEEK.",
".KKKKKKKKKKKKKK.",
"................",
]

# "i" in a blue disc: System information, info notifications
BASES["info"] = [
"................",
".....KKKKKK.....",
"...KKBBBBBBKK...",
"..KBBBBWWBBBBK..",
".KBBBBBWWBBBBBK.",
".KBBBBBBBBBBBBK.",
"KBBBBBWWWBBBBBBK",
"KBBBBBBWWBBBBBBK",
"KBBBBBBWWBBBBBBK",
"KBBBBBBWWBBBBBBK",
".KBBBBBWWBBBBBK.",
".KBBBBWWWWBBBBK.",
"..KBBBBBBBBBBK..",
"...KKBBBBBBKK...",
".....KKKKKK.....",
"................",
]

# yellow triangle with "!": warnings
BASES["warning"] = [
"................",
".......KK.......",
"......KYYK......",
"......KYYK......",
".....KYKKYK.....",
".....KYKKYK.....",
"....KYYKKYYK....",
"....KYYKKYYK....",
"...KYYYKKYYYK...",
"...KYYYYYYYYK...",
"..KYYYYKKYYYYK..",
"..KYYYYKKYYYYK..",
".KYYYYYYYYYYYYK.",
".KKKKKKKKKKKKKK.",
"................",
"................",
]

# red disc with a white cross: errors
BASES["error"] = [
"................",
".....KKKKKK.....",
"...KKRRRRRRKK...",
"..KRRRRRRRRRRK..",
".KRRWWRRRRWWRRK.",
".KRRWWWRRWWWRRK.",
"KRRRRWWWWWWRRRRK",
"KRRRRRWWWWRRRRRK",
"KRRRRRWWWWRRRRRK",
"KRRRRWWWWWWRRRRK",
".KRRWWWRRWWWRRK.",
".KRRWWRRRRWWRRK.",
"..KRRRRRRRRRRK..",
"...KKRRRRRRKK...",
".....KKKKKK.....",
"................",
]

# head and shoulders: profiles, users, artists, actors
BASES["person"] = [
"................",
"......KKKK......",
".....KOOOOK.....",
"....KOOOOOOK....",
"....KOKOOKOK....",
"....KOOOOOOK....",
"....KOOKKOOK....",
".....KOOOOK.....",
"......KKKK......",
"....KKBBBBKK....",
"...KBBBBBBBBK...",
"..KBBBBBBBBBBK..",
"..KBBBBBBBBBBK..",
"..KBBBBBBBBBBK..",
"..KKKKKKKKKKKK..",
"................",
]

# bell: Events (the event log)
BASES["events"] = [
"................",
".......KK.......",
"......KYYK......",
".....KYYYYK.....",
"....KYYYWYYK....",
"....KYYYWYYK....",
"....KYYYYYYK....",
"....KYYYYYYK....",
"...KYYYYYYYYK...",
"...KYYYYYYYYK...",
"..KYYYYYYYYYYK..",
".KyyyyyyyyyyyyK.",
".KKKKKKKKKKKKKK.",
"......KEEK......",
".......KK.......",
"................",
]

# spanner: system tools (the LibreELEC settings add-on)
BASES["tools"] = [
"................",
"..........KKK...",
".........KhhK.K.",
"........KhhK.KhK",
"........KhhKKhhK",
"........KhhhhhhK",
".......KhhhhhhK.",
"......KhhhKKKK..",
".....KhhhK......",
"....KhhhK.......",
"...KhhhK........",
"..KhhhK.........",
".KhhhK..........",
".KhhK...........",
"..KK............",
"................",
]

# satellite dish: Live TV / PVR
BASES["livetv"] = [
"................",
".KK.............",
".KhKK...........",
".KhhhKK......K..",
"..KhhhhK....K.K.",
"..KhhhhhK..K.K..",
"...KhhhhhKK.K...",
"...KhhhhhhKK....",
"....KhhhhhhK....",
".....KhhhhhhK...",
"......KKhhhhK...",
"........KKKK....",
".......KdK......",
"......KdddK.....",
".....KKKKKKK....",
"................",
]

# record in its sleeve: albums
BASES["album"] = [
"................",
".KKKKKKKKKK.....",
".KRRRRRRRRKKKK..",
".KRWWWWWWRKEEEK.",
".KRWRRRRWRKEEEEK",
".KRWRRRRWRKEhEEK",
".KRWWWWWWRKEhhEK",
".KRRRRRRRRKEhhEK",
".KRRRRRRRRKEhEEK",
".KRRRRRRRRKEEEEK",
".KRRRRRRRRKEEEK.",
".KRRRRRRRRKKKK..",
".KKKKKKKKKK.....",
"................",
"................",
"................",
]

# power symbol: the power menu
def _disc_outline(c, col):
    """Give every coloured pixel a black 4-neighbour edge."""
    fill = {(x, y) for y in range(16) for x in range(16) if c[y][x] == col}
    for (x, y) in fill:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < 16 and 0 <= ny < 16 and c[ny][nx] == ".":
                c[ny][nx] = "K"

c = blank()
for y in range(16):
    for x in range(16):
        d = ((x - 7.5) ** 2 + (y - 8.5) ** 2) ** 0.5
        if 4.2 <= d <= 6.4 and not (5 <= x <= 10 and y < 7):
            c[y][x] = "R"
for y in range(1, 9):
    c[y][7] = c[y][8] = "R"
_disc_outline(c, "R")
BASES["power"] = rows_of(c)

# alarm clock: timers
c = blank()
for y in range(16):
    for x in range(16):
        d = ((x - 7.5) ** 2 + (y - 8.5) ** 2) ** 0.5
        if d <= 6.2:
            c[y][x] = "W"
_disc_outline(c, "W")
for y in range(4, 9):
    c[y][7] = "K"
for x in range(8, 12):
    c[8][x] = "K"
c[1][2] = c[1][3] = c[2][2] = "K"; c[1][12] = c[1][13] = c[2][13] = "K"
BASES["clock"] = rows_of(c)

# ------------------------------------------------------------------ emblems
# 7x7 glyphs drawn inside a 9x9 black-edged badge in the bottom-right corner.
# Each has its own badge colour and glyph colour.

# ---- add-on tiles: original ArthurOS pictures for the kinds of add-on
# people put on the desktop (online video, media servers, games, radio,
# system tools). Deliberately not anyone's logo.

# monitor showing a globe with a play arrow: online video add-ons
BASES["addon_stream"] = [
"................",
".KKKKKKKKKKKKKK.",
".KhhhhhhhhhhhhK.",
".KhKKKKKKKKKKhK.",
".KhKCCGGCCCCKhK.",
".KhKCGGWCCGCKhK.",
".KhKCCGWWCGGKhK.",
".KhKCCGWWWGCKhK.",
".KhKCGGWWCCCKhK.",
".KhKCCGWCCGCKhK.",
".KhKKKKKKKKKKhK.",
".KhhhhhhhhhhhRK.",
".KKKKKKKKKKKKKK.",
"......KddK......",
"....KKKKKKKK....",
"................",
]

# tower server with drive bays and lights: media servers
BASES["server"] = [
"................",
"...KKKKKKKKKK...",
"...KhhhhhhhhK...",
"...KhKKKKKKhK...",
"...KhKddddKhK...",
"...KhKKKKKKhK...",
"...KhKKKKKKhK...",
"...KhKddddKhK...",
"...KhKKKKKKhK...",
"...KhhhhhhhhK...",
"...KhGhOhhhhK...",
"...KhhhhhhhhK...",
"...KhKKKKKKhK...",
"...KhhhhhhhhK...",
"...KKKKKKKKKK...",
"................",
]

# arcade cabinet: game launchers and emulators
BASES["addon_arcade"] = [
"................",
"....KKKKKKKK....",
"....KRRRRRRK....",
"....KYYYYYYK....",
"...KKKKKKKKKK...",
"...KhKKKKKKhK...",
"...KhKCBCBKhK...",
"...KhKBCBCKhK...",
"...KhKKKKKKhK...",
"..KKKKKKKKKKKK..",
"..KdKdRdddGdGK..",
"..KKKKKKKKKKKK..",
"...KhhhhhhhhK...",
"...KhhKKKKhhK...",
"...KhhhhhhhhK...",
"...KKKKKKKKKK...",
]

# circuit board with a chip: system and configuration add-ons
BASES["board"] = [
"................",
".KKKKKKKKKKKKKK.",
".KeGGGGGGGGGGeK.",
".KGYGGGGGGGGYGK.",
".KGGGKKKKKKGGGK.",
".KGYGKDDDDKGYGK.",
".KGYGKDWDDKGYGK.",
".KGYGKDDDDKGYGK.",
".KGGGKKKKKKGGGK.",
".KGGGGGYYGGGGGK.",
".KGhhGGGGGGhhGK.",
".KGhhGGGGGGhhGK.",
".KeGGGGGGGGGGeK.",
".KKKKKKKKKKKKKK.",
"................",
"................",
]

# transistor radio: music and radio add-ons
BASES["addon_radio"] = [
"................",
"..........K.....",
".........K......",
"........K.......",
"..KKKKKKKKKKKK..",
".KOOOOOOOOOOOOK.",
".KOKKKKKOOOKOOK.",
".KOKWdWKOOKYKOK.",
".KOKdWdKOOOKOOK.",
".KOKWdWKOOOOOOK.",
".KOKKKKKOhhhhOK.",
".KOOOOOOOOOOOOK.",
".KKKKKKKKKKKKKK.",
"..KK......KK....",
"................",
"................",
]

# P2
# tick: the selected-row mark in select lists. White with a black
# 4-neighbour edge (as _disc_outline draws), so the palette can tint it with
# colordiffuse (text on plain rows, textinv on the focused one) and it still
# reads on a light panel in the desktop icon picker.
BASES["tick"] = [
"................",
".............KK.",
"............KWWK",
"...........KWWWK",
"..........KWWWK.",
".K.......KWWWK..",
"KWK.....KWWWK...",
"KWWK...KWWWK....",
"KWWWK.KWWWK.....",
".KWWWKWWWK......",
"..KWWWWWK.......",
"...KWWWK........",
"....KWK.........",
".....K..........",
"................",
"................",
]

EMBLEMS = {
 "star":    ("B", "Y", ["...#...", "..###..", "#######", ".#####.", "..###..", ".##.##.", ".#...#."]),
 "clock":   ("W", "K", [".#####.", "#..#..#", "#..#..#", "#..##.#", "#.....#", "#.....#", ".#####."]),
 "search":  ("W", "K", [".###...", "#...#..", "#...#..", "#...#..", ".####..", "....##.", ".....##"]),
 "up":      ("G", "W", ["...#...", "..###..", ".#####.", "#######", "..###..", "..###..", "..###.."]),
 "refresh": ("B", "W", ["..###.#", ".#...##", "#...###", "#......", "#.....#", ".#...#.", "..###.."]),
 "zip":     ("Y", "K", ["..#.#..", "...#...", "..#.#..", "...#...", "..###..", "..#.#..", "..###.."]),
 "note":    ("W", "B", ["...###.", "...#.#.", "...#.#.", "...#...", ".###...", "####...", ".##...."]),
 "film":    ("W", "K", ["#######", "#.#.#.#", "#######", "#.....#", "#######", "#.#.#.#", "#######"]),
 "tag":     ("Y", "K", ["#####..", "#.#..#.", "#.....#", "#....#.", "#...#..", "#..#...", "####..."]),
 "calendar":("W", "R", [".#...#.", "#######", "#######", "#.#.#.#", "#######", "#.#.#.#", "#######"]),
 "flag":    ("W", "R", ["######.", "#######", "######.", "#......", "#......", "#......", "#......"]),
 "building":("W", "K", ["...#...", "..###..", ".#####.", ".#.#.#.", ".#.#.#.", ".#.#.#.", "#######"]),
 "clapper": ("W", "K", ["#.#.#.#", "#######", ".......", "#######", "#.....#", "#.....#", "#######"]),
 "stack":   ("W", "K", ["..#####", "..#...#", "#####.#", "#...#.#", "#...###", "#...#..", "#####.."]),
 "globe":   ("C", "K", ["..###..", ".#.#.#.", "#..#..#", "#######", "#..#..#", ".#.#.#.", "..###.."]),
 "gear":    ("W", "D", ["...#...", ".#####.", ".##.##.", "###.###", ".##.##.", ".#####.", "...#..."]),
 "info":    ("B", "W", ["...#...", ".......", "..##...", "...#...", "...#...", "...#...", "..###.."]),
 "cross":   ("R", "W", ["##...##", "###.###", ".#####.", "..###..", ".#####.", "###.###", "##...##"]),
 "crown":   ("W", "O", ["#..#..#", "##.#.##", "#######", "#######", "#######", ".......", "#######"]),
 "letter":  ("W", "K", ["..###..", ".#...#.", "#.....#", "#######", "#.....#", "#.....#", "#.....#"]),
 "speaker": ("W", "K", ["...#...", "..##...", "####.#.", "####..#", "####.#.", "..##...", "...#..."]),
 "camera":  ("W", "K", ["..##...", "#######", "#..#..#", "#.###.#", "#..#..#", "#######", "......."]),
 "eye":     ("W", "K", [".......", "..###..", ".#...#.", "#..#..#", ".#...#.", "..###..", "......."]),
 "pad":     ("W", "K", [".......", ".#####.", "#.#...#", "###.#.#", "#.#...#", ".##.##.", "......."]),
 "plug":    ("W", "K", [".#...#.", ".#...#.", "#######", "#######", ".#####.", "..###..", "...#..."]),
 "book":    ("W", "B", ["##...##", "#.#.#.#", "#..#..#", "#..#..#", "#..#..#", "#..#..#", ".##.##."]),
 "list":    ("W", "K", ["#.#####", ".......", "#.#####", ".......", "#.#####", ".......", "#.#####"]),
 "play":    ("G", "W", ["#......", "###....", "#####..", "#######", "#####..", "###....", "#......"]),
 "record":  ("W", "R", ["..###..", ".#####.", "#######", "#######", "#######", ".#####.", "..###.."]),
 "wave":    ("W", "B", [".......", ".##....", "#..#..#", "....##.", ".##....", "#..#..#", "....##."]),
 "box":     ("O", "K", ["#######", "#.....#", "#######", "#.....#", "#..#..#", "#.....#", "#######"]),
 "wrench":  ("W", "K", [".#...#.", ".##.##.", "..###..", "...#...", "..#....", ".#.....", "#......"]),
 "bubble":  ("W", "K", ["#######", "#.....#", "#.###.#", "#.....#", "#######", ".##....", ".#....."]),
 "palette": ("W", "R", [".#####.", "#.#.#.#", "#.....#", "#.#..##", "#....#.", ".####..", "......."]),
 "window":  ("W", "B", ["#######", "#######", "#.....#", "#.....#", "#.....#", "#.....#", "#######"]),
 "trash":   ("W", "K", [".#####.", "#######", ".#.#.#.", ".#.#.#.", ".#.#.#.", ".#.#.#.", ".#####."]),
 "bolt":    ("K", "Y", ["...###.", "..###..", ".###...", "#######", "...###.", "..###..", ".##...."]),
 "hash":    ("W", "K", [".#..#..", "#######", ".#..#..", ".#..#..", "#######", ".#..#..", "......."]),
 "link":    ("W", "K", ["...####", ".....##", "....#.#", "...#..#", "..#....", ".#.....", "#......"]),
 "heart":   ("W", "R", [".##.##.", "#######", "#######", "#######", ".#####.", "..###..", "...#..."]),
 "down":    ("G", "W", ["..###..", "..###..", "..###..", "#######", ".#####.", "..###..", "...#..."]),
 "check":   ("G", "W", ["......#", ".....##", "#...##.", "##.##..", ".###...", "..#....", "......."]),
 "minus":   ("W", "K", [".......", ".......", ".......", "#######", ".......", ".......", "......."]),
 "moon":    ("n", "Y", ["..###..", ".##....", "##.....", "##.....", "##.....", ".##....", "..###.."]),
 "snow":    ("C", "W", ["#..#..#", ".#.#.#.", "..###..", "#######", "..###..", ".#.#.#.", "#..#..#"]),
 "lock":    ("W", "K", ["..###..", ".#...#.", ".#...#.", "#######", "###.###", "###.###", "#######"]),
}

def badge(base, emblem):
    bg, fg, glyph = EMBLEMS[emblem]
    c = [list(r) for r in base]
    rect(c, 7, 7, 15, 15, fill=bg)
    for y, r in enumerate(glyph):
        for x, ch in enumerate(r):
            if ch == "#":
                c[8 + y][8 + x] = fg
    return rows_of(c)

# --------------------------------------------------------------- registry
# name: base  |  (base, emblem)
SPEC = {
 # ---- Home tiles and their families
 "movies_titles": ("movies", "list"),   "movies_recent": ("movies", "star"),
 "movies_genres": ("movies", "tag"),    "movies_sets": ("movies", "stack"),
 "movies_years": ("movies", "calendar"),"movies_info": ("movies", "info"),
 "tvshows_titles": ("tvshows", "list"), "tvshows_recent": ("tvshows", "star"),
 "tvshows_inprogress": ("tvshows", "clock"), "tvshows_genres": ("tvshows", "tag"),
 "tvshows_fanart": ("tvshows", "camera"), "tvshows_info": ("tvshows", "info"),
 "music_songs": ("music", "list"),      "music_genres": ("music", "tag"),
 "music_recent": ("music", "star"),     "music_played": ("music", "clock"),
 "music_years": ("music", "calendar"),  "music_compilations": ("music", "stack"),
 "music_top100_songs": ("music", "crown"), "music_lyrics": ("music", "bubble"),
 "music_visualisation": ("music", "eye"), "music_party": ("music", "bolt"),
 "music_artists": ("person", "note"),   "music_roles": ("person", "list"),
 "artist_info": ("person", "info"),     "actor": ("person", "star"),
 "user": ("person", "check"),
 "music_albums": ("album", "note"),     "album_info": ("album", "info"),
 "music_top100_albums": ("album", "crown"),
 "musicvideos_titles": ("musicvideos", "list"), "musicvideos_recent": ("musicvideos", "star"),
 "musicvideos_info": ("musicvideos", "info"),
 "video_files": ("folder", "film"),     "video_deleted": ("video", "trash"),
 "video_versions": ("video", "stack"),  "video_subtitles": ("video", "bubble"),
 "video_cover": ("video", "camera"),
 "pictures_files": ("folder", "camera"),"screenshot": ("pictures", "camera"),
 "pictures_collections": ("pictures", "stack"), "pictures_decoder": ("pictures", "gear"),
 "playlist_music": ("playlist", "note"),"playlist_video": ("playlist", "film"),
 "music_files": ("folder", "note"),     "programs_files": ("folder", "window"),
 # ---- add-ons
 "addons_all": ("addons_user", "list"), "addons_video": ("addons", "film"),
 "addons_music": ("addons", "note"),    "addons_pictures": ("addons", "camera"),
 "addons_program": ("addons", "window"),"addons_game": ("addons", "pad"),
 "addons_repo": ("addons", "box"),      "addons_search": ("addons", "search"),
 "addons_zip": ("addons", "zip"),       "addons_updates": ("addons", "up"),
 "addons_recent": ("addons", "clock"),  "addons_check": ("addons", "refresh"),
 "addons_none": ("addons", "cross"),    "addons_service": ("addons", "gear"),
 "addons_skin": ("addons", "palette"),  "addons_context": ("addons", "list"),
 "addons_helper": ("addons", "wrench"), "addons_library": ("addons", "book"),
 "addons_peripheral": ("program", "plug"),
 "audio_decoder": ("audio", "gear"),    "audio_encoder": ("audio", "record"),
 "file_font": ("file", "letter"),       "file_info": ("file", "info"),
 "file_mimetype": ("file", "tag"),      "file_script": ("file", "play"),
 "file_shortcut": ("file", "link"),
 "language": ("network", "letter"),     "info_provider": ("network", "info"),
 "inputstream": ("network", "wave"),    "vfs": ("harddisk", "globe"),
 "removable": ("harddisk", "plug"),     "library_info": ("media", "info"),
 "lookandfeel": ("interface", "palette"), "uisounds": ("interface", "speaker"),
 "screensaver": ("system", "eye"),      "webinterface": ("network", "window"),
 "weather_provider": ("weather", "info"),
 # ---- generic library nodes
 "genre": ("folder", "tag"),            "year": ("folder", "calendar"),
 "studio": ("folder", "building"),      "country": ("folder", "flag"),
 "director": ("folder", "clapper"),     "tags": ("folder", "hash"),
 "music_top100": ("folder", "crown"),
 # ---- discs
 "disc_empty": ("disc", "cross"),       "disc_dvd": ("disc", "film"),
 "disc_bluray": ("disc", "star"),       "disc_vcd": ("disc", "play"),
 "disc_cdda": ("disc", "note"),
 # ---- live TV
 "pvr_channels": ("livetv", "list"),    "pvr_guide": ("livetv", "calendar"),
 "pvr_recordings": ("livetv", "record"),"pvr_timers": ("livetv", "clock"),
 "pvr_timerrules": ("livetv", "gear"),  "pvr_search": ("livetv", "search"),
 "pvr_client": ("livetv", "plug"),
 "games_addons": ("games", "list"),
 # ---- the power menu
 "power_suspend": ("power", "moon"),    "power_hibernate": ("power", "snow"),
 "power_reboot": ("power", "refresh"),  "power_inhibit": ("power", "lock"),
 "power_allow": ("power", "check"),     "exit": ("interface", "cross"),
 "timer_cancel": ("clock", "cross"),    "logoff": ("person", "cross"),
 "masterlock": ("settings", "lock"),
 # ---- window title bars
 "pvr_info": ("livetv", "info"),        "pvr_manager": ("livetv", "wrench"),
 "pvr_groups": ("livetv", "stack"),     "pvr_controls": ("livetv", "play"),
 "osd_video": ("video", "play"),        "osd_music": ("music", "play"),
 "osd_game": ("games", "play"),         "file_list": ("file", "list"),
 "download": ("file", "down"),          "calibration": ("interface", "gear"),
 "smartplaylist": ("playlist", "gear"), "smartrule": ("playlist", "tag"),
 "bookmarks": ("video", "flag"),        "addons_info": ("addons", "info"),
 "controllers": ("games", "plug"),      "numeric": ("file", "hash"),
 "rds": ("audio", "info"),              "pictures_info": ("pictures", "info"),
 "process_info": ("system", "info"),    "audio_muted": ("audio", "cross"),
 "pvr_radio": ("livetv", "note"),       "desktop_edit": ("interface", "wrench"),
 "addon_server": ("server", "play"),    "addon_config": ("board", "wrench"),    "seek": ("player", "clock"),
}

def build(icons):
    """icons: the original mkmedia ICONS dict. Returns the full registry."""
    reg = dict(icons)
    reg.update(BASES)
    reg["musicvideos"] = recolour(icons["movies"], "Cbe", "Mmp")
    for name, spec in SPEC.items():
        base, emblem = spec
        reg[name] = badge(reg[base], emblem)
    for name, rows in reg.items():
        assert len(rows) == 16 and all(len(r) == 16 for r in rows), name
    return reg

# ------------------------------------------------------ Kodi's fallbacks
DEFAULT_MAP = {
 "DefaultFolder": "folder", "DefaultFolderBack": "parent",
 "DefaultVideo": "video", "DefaultVideoCover": "video_cover",
 "DefaultMovies": "movies", "DefaultMovieTitle": "movies_titles",
 "DefaultTVShows": "tvshows", "DefaultTVShowTitle": "tvshows_titles",
 "DefaultSets": "movies_sets",
 "DefaultMusicSongs": "music_songs", "DefaultMusicAlbums": "music_albums",
 "DefaultMusicArtists": "music_artists", "DefaultAudio": "audio",
 "DefaultAudioCover": "album", "DefaultAlbumCover": "album",
 "DefaultArtist": "music_artists",
 "DefaultPicture": "pictures", "DefaultPictures": "pictures",
 "DefaultAddon": "addons", "DefaultAddonNone": "addons_none",
 "DefaultAddonProgram": "addons_program", "DefaultAddonService": "addons_service",
 "DefaultAddonSkin": "addons_skin", "DefaultFile": "file",
 "DefaultHardDisk": "harddisk", "DefaultNetwork": "network",
 "DefaultProgram": "program", "DefaultPlaylist": "playlist",
 "DefaultMusicPlaylists": "playlist_music", "DefaultVideoPlaylists": "playlist_video",
 "DefaultFavourites": "favourites",
 "DefaultDVDEmpty": "disc_empty", "DefaultDVDFull": "disc_dvd", "DefaultDVDRom": "disc",
 "DefaultRemovableDisk": "removable",
 "DefaultGenre": "genre", "DefaultYear": "year", "DefaultStudios": "studio",
 "DefaultCountry": "country", "DefaultDirector": "director", "DefaultActor": "actor",
 "DefaultTags": "tags",
 "DefaultInProgressShows": "tvshows_inprogress",
 "DefaultRecentlyAddedEpisodes": "tvshows_recent",
 "DefaultRecentlyAddedMovies": "movies_recent",
 "DefaultRecentlyAddedMusicVideos": "musicvideos_recent",
 "DefaultMusicVideos": "musicvideos",
 "DefaultMusicCompilations": "music_compilations",
 "DefaultMusicRecentlyAdded": "music_recent", "DefaultMusicTop100": "music_top100",
 "DefaultMusicYears": "music_years", "DefaultMusicGenres": "music_genres",
 "DefaultScript": "file_script", "DefaultShortcut": "file_shortcut",
 "DefaultTVShowsFanart": "tvshows_fanart", "DefaultWeather": "weather",
 "DefaultIconError": "error", "DefaultIconInfo": "info", "DefaultIconWarning": "warning",
 "DefaultPVRChannels": "pvr_channels", "DefaultPVRRecordings": "pvr_recordings",
 "DefaultPVRGuide": "pvr_guide", "DefaultPVRTimers": "pvr_timers",
 "DefaultTvRecordings": "pvr_recordings",
 "DefaultScreenshot": "screenshot", "DefaultProfile": "person", "DefaultUser": "user",
 "DefaultGame": "games", "DefaultGames": "games_addons", "DefaultAddonGame": "addons_game",
 "DefaultAddSource": "addsource",
 "DefaultAddonAlbumInfo": "album_info", "DefaultAddonArtistInfo": "artist_info",
 "DefaultAddonAudioDecoder": "audio_decoder", "DefaultAddonAudioEncoder": "audio_encoder",
 "DefaultAddonContextItem": "addons_context", "DefaultAddonFont": "file_font",
 "DefaultAddonHelper": "addons_helper", "DefaultAddonImageDecoder": "pictures_decoder",
 "DefaultAddonImages": "pictures_collections", "DefaultAddonInfoLibrary": "library_info",
 "DefaultAddonInfoProvider": "info_provider", "DefaultAddonInputstream": "inputstream",
 "DefaultAddonLanguage": "language", "DefaultAddonLibrary": "addons_library",
 "DefaultAddonLookAndFeel": "lookandfeel", "DefaultAddonLyrics": "music_lyrics",
 "DefaultAddonMovieInfo": "movies_info", "DefaultAddonMusic": "addons_music",
 "DefaultAddonMusicVideoInfo": "musicvideos_info", "DefaultAddonPVRClient": "pvr_client",
 "DefaultAddonPeripheral": "addons_peripheral", "DefaultAddonPicture": "addons_pictures",
 "DefaultAddonRepository": "addons_repo", "DefaultAddonScreensaver": "screensaver",
 "DefaultAddonSubtitles": "video_subtitles", "DefaultAddonTvInfo": "tvshows_info",
 "DefaultAddonUISounds": "uisounds", "DefaultAddonVfs": "vfs",
 "DefaultAddonVideo": "addons_video", "DefaultAddonVisualization": "music_visualisation",
 "DefaultAddonWeather": "weather_provider", "DefaultAddonWebSkin": "webinterface",
 "DefaultAddonsInstalled": "addons_user", "DefaultAddonsRecentlyUpdated": "addons_recent",
 "DefaultAddonsRepo": "addons_repo", "DefaultAddonsSearch": "addons_search",
 "DefaultAddonsUpdates": "addons_updates", "DefaultAddonsZip": "addons_zip",
 "DefaultBluray": "disc_bluray", "DefaultCDDA": "disc_cdda",
 "DefaultExtensionInfo": "file_info", "DefaultMimetypeInfo": "file_mimetype",
 "DefaultMusicRecentlyPlayed": "music_played", "DefaultMusicRoles": "music_roles",
 "DefaultMusicSources": "music_files",
 "DefaultMusicTop100Albums": "music_top100_albums",
 "DefaultMusicTop100Songs": "music_top100_songs",
 "DefaultMusicVideoTitle": "musicvideos_titles",
 "DefaultPVRSearch": "pvr_search", "DefaultPVRTimerRules": "pvr_timerrules",
 "DefaultPartyMode": "music_party",
 "DefaultVCD": "disc_vcd",
 "DefaultVideoDeleted": "video_deleted", "DefaultVideoVersions": "video_versions",
}

# Kodi names that deliberately share one icon, because to the viewer they are
# the same thing. Anything not listed here must be pixel-unique.
ALIASES = {
 frozenset({"DefaultAudioCover", "DefaultAlbumCover"}):
     "both are 'an album with no cover art'",
 frozenset({"DefaultArtist", "DefaultMusicArtists"}):
     "both are 'a music artist with no picture'",
 frozenset({"DefaultPicture", "DefaultPictures"}):
     "both are 'a picture with no thumbnail'",
 frozenset({"DefaultPVRRecordings", "DefaultTvRecordings"}):
     "the old and new names for a TV recording",
 frozenset({"DefaultAddonRepository", "DefaultAddonsRepo"}):
     "both mean 'add-on repositories'",
}

# ------------------------------------------------------ window title icons
# The icon on each window's title bar. themepass.py applies these, so hand-
# built and generated windows alike get a picture of what they are.
WINDOW_ICONS = {
 "AddonBrowser": "addons", "DialogAddonInfo": "addons_info",
 "DialogAddonSettings": "addons_helper", "DialogBusy": "clock",
 "DialogButtonMenu": "power", "DialogColorPicker": "skin", "DialogConfirm": "info",
 "DialogContextMenu": "file_list", "DialogExtendedProgressBar": "download",
 "DialogFullScreenInfo": "file_info", "DialogGameControllers": "controllers",
 "DialogKeyboard": "file_font", "DialogMediaSource": "addsource",
 "DialogMusicInfo": "album_info", "DialogNumeric": "numeric",
 "DialogPVRChannelGuide": "pvr_guide", "DialogPVRChannelManager": "pvr_manager",
 "DialogPVRChannelsOSD": "pvr_channels", "DialogPVRGroupManager": "pvr_groups",
 "DialogPVRGuideControls": "pvr_controls", "DialogPVRGuideSearch": "pvr_search",
 "DialogPVRInfo": "pvr_info", "DialogPVRRadioRDSInfo": "rds",
 "DialogPictureInfo": "pictures_info", "DialogPlayerProcessInfo": "process_info",
 "DialogSeekBar": "seek", "DialogSelect": "playlist", "DialogSettings": "settings",
 "DialogSlider": "player", "DialogSubtitles": "video_subtitles",
 "DialogTextViewer": "file", "DialogVideoInfo": "movies_info",
 "DialogVideoManager": "video_versions", "EventLog": "events",
 "FileBrowser": "folder", "FileManager": "harddisk", "GameOSD": "osd_game",
 "LoginScreen": "person", "MusicOSD": "osd_music", "MyFavourites": "favourites",
 "MyGames": "games", "MyMusicNav": "music", "MyMusicPlaylistEditor": "playlist_music",
 "MyPVRChannels": "pvr_channels", "MyPVRGuide": "pvr_guide",
 "MyPVRRecordings": "pvr_recordings", "MyPVRSearch": "pvr_search",
 "MyPVRTimers": "pvr_timers", "MyPics": "pictures", "MyPlaylist": "playlist_video",
 "MyPrograms": "program", "MyVideoNav": "video", "MyWeather": "weather",
 "PlayerControls": "player", "Settings": "settings",
 "SettingsProfile": "user", "SettingsScreenCalibration": "calibration",
 "SettingsSystemInfo": "info", "SkinSettings": "skin",
 "SmartPlaylistEditor": "smartplaylist", "SmartPlaylistRule": "smartrule",
 "VideoOSD": "osd_video", "VideoOSDBookmarks": "bookmarks",
}
# windows whose title icon follows what they are showing
WINDOW_ICON_EXPR = {
 "SettingsCategory": "$VAR[ArthurWindowIcon]",
}
