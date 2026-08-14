import io, os
SRC="guide/src"; FONTS="/tmp/claude-0/-home-user-nanobanana-mcp/90335711-4b4e-5366-bbb5-4e261c51b9ba/scratchpad/fonts/fonts.css"
order=["head.html","body-01-hero-diagnosis.html","body-02-map.html","body-03-routine.html",
       "body-04-tech.html","body-05-products.html","body-06-tools.html","body-07-skin.html",
       "body-08-video.html","body-09-dont.html","body-99-footer.html"]
parts=[]
for f in order:
    p=os.path.join(SRC,f)
    if not os.path.exists(p): raise SystemExit("MISSING "+p)
    parts.append(open(p,encoding="utf-8").read())
html="\n".join(parts)
html=html.replace("/*FONTS*/", open(FONTS,encoding="utf-8").read())
open("guide/makeup-guide.html","w",encoding="utf-8").write(html)
print(f"built guide/makeup-guide.html  {len(html)/1024:.0f}KB  ({len(html.encode())/1048576:.2f}MB)")
