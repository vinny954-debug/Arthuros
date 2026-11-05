#!/usr/bin/env python3
"""Write the US English strings from the UK English source.

Kodi picks a skin's strings by the interface language: with Kodi set to
English (US) it reads resource.language.en_us, and any string left
untranslated falls back to en_gb. Kodi's own strings (Favourites, Colours...)
switch the same way, from Kodi's en_us language add-on.
"""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(HERE, "skin.arthuros", "language")
SPELL = [("colour", "color"), ("Colour", "Color"), ("favourite", "favorite"),
         ("Favourite", "Favorite"), ("bevelled", "beveled"), ("centre", "center"),
         ("Centre", "Center"), ("grey", "gray"), ("Grey", "Gray"),
         ("customis", "customiz"), ("Customis", "Customiz"), ("organis", "organiz"),
         ("behaviour", "behavior"), ("licence", "license"), ("programme", "program")]
src = open(os.path.join(L, "resource.language.en_gb", "strings.po")).read()
head, _, body = src.partition('msgctxt "#')
head = head.replace("Language: en_GB", "Language: en_US")
out, n = [head], 0
for block in re.split(r'(?=msgctxt "#)', 'msgctxt "#' + body):
    m = re.search(r'msgid "(.*)"\nmsgstr ""', block)
    if not m:
        out.append(block); continue
    us = m.group(1)
    for a, b in SPELL:
        us = us.replace(a, b)
    if us != m.group(1):
        block = block.replace('msgstr ""', f'msgstr "{us}"', 1); n += 1
    out.append(block)
d = os.path.join(L, "resource.language.en_us")
os.makedirs(d, exist_ok=True)
open(os.path.join(d, "strings.po"), "w").write("".join(out))
print(f"lang: en_us written, {n} strings respelled")
