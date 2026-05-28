# Nano Banana Image Prompts — Restylane Deck

These prompts produce photorealistic, AAA-Academy-style face illustrations
to replace the abstract vector medallions in the product slides. Run them
on a machine where the nano-banana MCP can write images to disk (your local
clinic workstation, with `GEMINI_API_KEY` set), then drag each output into
the matching slide as the new "hero" image on the left panel.

Use `aspectRatio: 4:5` and `imageSize: 2K` for crisp, portrait-oriented
hero images. Each prompt is self-contained.

---

## 1. Title slide — clinical hero

```
Editorial medical aesthetic photograph, soft beige travertine marble
background, warm cream lighting, an elegant clear glass vial of clear
hyaluronic-acid filler resting on a polished marble surface, gold-rim
detail, no text, no labels, no logos, premium pharmaceutical product
photography style, professional, calm, luxurious. 16:9.
```

## 2. Restylane Lyft — Bone Mimicry

```
Editorial medical aesthetic illustration, side profile portrait of a young
woman, hair pulled back in a low bun, facing left, smooth bare skin, neutral
makeup, no jewelry, soft beauty lighting, beige travertine background, ample
empty space on the right of the frame for text. Overlaid on her jawline and
chin: a crisp white geometric triangle outline tracing ear → chin → jaw
angle. Thin elegant white lines with subtle glow. No text, no labels, no
logos. Cinematic, premium medical training aesthetic. 16:9.
```

## 3. Restylane Defyne — Tissue Mimicry

```
Editorial medical aesthetic illustration, side profile portrait of a young
woman, facing right, smooth skin, neutral makeup, soft warm lighting, beige
travertine background, ample empty space on the left for text. Overlaid on
her lower face (jowl + marionette area): a soft purple geometric mesh
pattern that follows the skin contour, suggesting flexible tissue support.
The mesh is fine, slightly transparent, gentle purple. No text, no labels,
no logos. Premium medical training aesthetic. 16:9.
```

## 4. Restylane Volyme — Soft Cheek Volume

```
Editorial medical aesthetic illustration, three-quarter portrait of a young
woman, facing slightly left, smooth bare skin, neutral makeup, soft natural
lighting, beige travertine background. Overlaid on her cheek (zygomatic
midface area): a soft glowing translucent purple-blue radial gradient
suggesting filled soft volume — like a gentle inner glow, not a hard shape.
No text, no labels, no logos. Premium medical aesthetic photography. 16:9.
```

## 5. Restylane Kysse — Lip Dynamics

```
Editorial close-up photograph of a young woman's mouth and chin, neutral
soft makeup with naturally-colored lips, soft beauty lighting, beige
travertine background visible at edges. The lips are slightly parted in a
relaxed expression — natural, dynamic, not over-filled. Subtle purple line
overlay highlighting the vermillion border. No text, no labels, no logos.
Premium clinical photography. 4:3.
```

## 6. Restylane Eyelight — Tear-Trough

```
Editorial close-up photograph of the upper face of a young woman — eye and
under-eye area — facing forward, neutral makeup, soft beauty lighting,
beige travertine background. A soft thin blue crescent overlay sits just
under the lower eyelid (tear-trough region), subtle and elegant. The skin
is smooth, no visible filler bumps. No text, no labels, no logos. Premium
clinical photography. 4:3.
```

## 7. Restylane Refyne — Dynamic Wrinkle Support

```
Editorial medical aesthetic photograph, three-quarter portrait of a young
woman in motion of a soft smile, facing forward-left, neutral makeup, soft
warm lighting, beige travertine background. Overlaid in the nasolabial fold
area: three soft purple curved lines suggesting where dynamic wrinkles
form. Lines are thin, elegant, slightly glowing. No text, no labels, no
logos. Premium aesthetic. 16:9.
```

## 8. Restylane Classic — Fine Lines

```
Editorial medical aesthetic photograph, neutral portrait of a young woman,
facing forward, smooth bare skin, neutral makeup, beige travertine
background. Overlaid: thin elegant deep-blue lines marking subtle perioral
and forehead fine lines. The look is refined, gentle, classical. No text,
no labels, no logos. Premium clinical aesthetic. 16:9.
```

## 9. Skinboosters Vital / Vital Light — Biorevitalization

```
Editorial macro photograph of beautiful glowing healthy skin texture on a
woman's cheek, soft warm beauty lighting, beige travertine background.
Overlaid: a fine scatter of small luminous blue micro-droplet dots across
the cheek, suggesting injection points. The dots are tiny, elegant,
evenly distributed in a circular pattern. No text, no labels, no logos.
Premium medical aesthetic. 4:5.
```

## 10. Face Map — Frontal Aesthetic Chart

```
Editorial frontal portrait illustration of a young woman, neutral
expression, hair pulled back, neutral makeup, smooth skin, beige
travertine background. The face is composed and symmetric, facing the
camera directly. Vintage anatomical illustration style — clean, classical,
slightly hand-drawn. Soft warm tones. No text, no labels, no logos. 16:9.
```

## 11. Gel structure — NASHA grains

```
Macro scientific illustration of NASHA-style hyaluronic-acid gel under
microscope — irregular, gel-like granular particles in clear medium, soft
blue tones, biological aesthetic. Clean medical illustration style, no
text, no labels. 1:1.
```

## 12. Gel structure — OBT smooth mesh

```
Macro scientific illustration of an OBT-style continuous crosslinked
hyaluronic-acid gel network — a smooth interconnected polymer mesh,
purple-pink tones, biological aesthetic. Clean medical illustration
style, no text, no labels. 1:1.
```

---

## How to swap into the deck

1. Generate each image with nano-banana on your local machine.
2. In PowerPoint / Keynote, open `Restylane_Clinical_Reference_AAA.pptx`.
3. On each product slide, delete the medallion shapes inside the left
   panel (the circle + abstract icon).
4. Insert the matching nano-banana image, scaled to fill the panel.
5. The Hebrew/Latin text labels, family chip, data card on the right, and
   header all stay in place.

If you want me to wire this up automatically the next time my container
has `GEMINI_API_KEY` and disk-writeable image returns, just say "regenerate
the deck with photorealistic faces" and I'll handle it end-to-end.
