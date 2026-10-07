import json, sys, pathlib
d = pathlib.Path(__file__).parent
src = (d/"app.src.html").read_text()
eng = (d/"engine.js").read_text().replace("</script", "<\\/script")
data = json.dumps(json.loads((d/"data.json").read_text()), ensure_ascii=False, separators=(",",":"))
out = src.replace("/*ENGINE*/", eng).replace("/*DATA*/", data)
mode = sys.argv[1] if len(sys.argv) > 1 else "publish"
if mode == "local":   # test harness: vendor copies instead of CDN, wrapped as a full document
    out = out.replace("https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/", "vendor/pdfjs-dist-3.11.174/package/build/")
    out = out.replace("https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js", "vendor/xlsx-0.18.5/package/dist/xlsx.full.min.js")
    out = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + out + "</body></html>"
    (d/"local.html").write_text(out)
else:
    (d/"osh-simulator.html").write_text(out)
print(mode, len(out))
