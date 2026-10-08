import httpx
B = "http://127.0.0.1:8100"
c = httpx.Client(base_url=B, timeout=300, trust_env=False, headers={"X-Actor": "smoke-real"})
projs = c.get("/api/v1/projects").json()["items"]
proj = next(p for p in projs if p["name"] == "E Smoke")
product = c.get(f"/api/v1/projects/{proj['id']}/products").json()["items"][0]
image_id = c.get(f"/api/v1/projects/{proj['id']}/products/{product['id']}/images").json()["items"][0]["id"]
print("project:", proj["name"], "| source image:", image_id)
gen = c.post(
    f"/api/v1/projects/{proj['id']}/products/{product['id']}/creatives/generate",
    json={"asset_type": "main_image_edit", "source_image_ids": [image_id]},
)
print("generate status:", gen.status_code)
if gen.status_code >= 400:
    print("detail:", gen.text[:400])
else:
    cr = gen.json()
    print("model:", cr.get("model"), "| consistency:", cr.get("consistency_status"),
          "| compliance:", cr.get("compliance_status"), "| size:",
          f"{cr.get('width')}x{cr.get('height')}", "| bytes:", cr.get("size_bytes"))
    c.post(f"/api/v1/projects/{proj['id']}/creatives/{cr['id']}/approve")
    dl = c.get(f"/api/v1/projects/{proj['id']}/creatives/{cr['id']}/download")
    out = r"C:\Users\Zqr\Documents\Codex\2026-09-13\ai-ai-listing\apps\api\data\local\outputs\gpt-image-2-main.png"
    import os
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "wb").write(dl.content)
    print("downloaded:", dl.status_code, "->", out, f"({len(dl.content)} bytes)")
    print("prompt:", cr.get("prompt"))
