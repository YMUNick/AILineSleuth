"""Drive the running app with Playwright (Edge) and capture the demo states.

Used for the pitch deck screenshots (docs/pitch/deck/assets/) and for layout QA
at projector resolutions. Start the app first, e.g. in offline-fixture mode:

    AGENT_MODE=offline_fixture FIXTURE_STEP_DELAY_S=0.8 python -m uvicorn app.main:app --port 8000

Then:

    python docs/pitch/deck/capture-screens.py --out docs/pitch/deck/assets --sizes 1920x1080
    python docs/pitch/deck/capture-screens.py --out <qa-dir> --sizes 1280x720,1366x768,758x922 --qa

Needs `pip install playwright` (uses the installed Microsoft Edge, no browser download).
Screenshots taken in offline-fixture mode show the yellow OFFLINE FIXTURE banner unless
--hide-fixture-banner is passed; never present those as real Gemini output.
"""

import argparse
import json
import os

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
LAYOUT_PROBE = """() => {
  const r = {};
  const doc = document.documentElement;
  r.viewport = [innerWidth, innerHeight];
  r.hScroll = doc.scrollWidth > innerWidth + 1;
  r.vScroll = doc.scrollHeight > innerHeight + 1;
  const covered = (id) => {
    const el = document.getElementById(id);
    if (!el || !el.offsetParent) return 'hidden';
    const b = el.getBoundingClientRect();
    const hit = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
    return hit && (el === hit || el.contains(hit)) ? 'ok' : 'covered';
  };
  r.investigate = covered('investigate');
  r.createWo = covered('create-wo');
  const over = [];
  document.querySelectorAll('#alert, #downtime-box, #downtime, .card, #result').forEach((el) => {
    if (el.scrollWidth > el.clientWidth + 1) over.push(el.id || el.className);
  });
  r.overflowX = over.slice(0, 8);
  return r;
}"""


def wait_done(page, timeout=90_000):
    page.wait_for_function(
        "() => { const c = document.getElementById('status-chip');"
        " return c && /root cause found|insufficient evidence|failed/i.test(c.textContent); }",
        timeout=timeout,
    )
    page.wait_for_timeout(3500)  # let reveal / highlight animations settle


def reset(page, scenario):
    page.goto(BASE + "/")
    page.wait_for_load_state("networkidle")
    page.select_option("#scenario", scenario)
    page.wait_for_timeout(300)
    if page.is_visible("#reset"):
        page.click("#reset")
    page.wait_for_timeout(1200)


def capture(browser, size, out, qa, hide_banner):
    w, h = size
    ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
    page = ctx.new_page()
    report = {"size": f"{w}x{h}"}
    tag = "" if not qa else f"{w}x{h}-"

    def shot(name):
        if hide_banner:
            page.add_style_tag(content="#fixture-banner{display:none!important}")
        page.screenshot(path=os.path.join(out, f"{tag}{name}.png"))

    # Main story: Line 2 over-temperature
    reset(page, "R01")
    report["idle"] = page.evaluate(LAYOUT_PROBE)
    shot("01-overview")
    page.click("#investigate")
    page.wait_for_timeout(2600)
    shot("02-investigating")
    wait_done(page)
    report["done"] = page.evaluate(LAYOUT_PROBE)
    shot("03-root-cause")
    shot("04-conclusion")
    wo_url = None
    if page.is_visible("#create-wo"):
        page.click("#create-wo")
        page.wait_for_selector("#qr-url", state="visible", timeout=15_000)
        page.wait_for_timeout(800)
        shot("06-wo-modal")
        wo_url = page.text_content("#qr-url")
        if page.is_visible("#show-summary"):
            page.click("#show-summary")
            page.wait_for_selector("#recap", state="visible", timeout=10_000)
            page.wait_for_timeout(2500)
            report["recap"] = page.evaluate(LAYOUT_PROBE)
            shot("05-before-after")
    # Healthy data: grey card
    reset(page, "N01")
    page.click("#investigate")
    wait_done(page)
    report["grey"] = page.evaluate(LAYOUT_PROBE)
    shot("07-insufficient")
    ctx.close()

    # Phone work order page
    if wo_url and not qa:
        path = wo_url[wo_url.find("/wo/"):] if "/wo/" in wo_url else None
        if path:
            m = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
            mp = m.new_page()
            mp.goto(BASE + path)
            mp.wait_for_load_state("networkidle")
            mp.wait_for_timeout(800)
            mp.screenshot(path=os.path.join(out, "06-work-order-phone.png"))
            m.close()
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sizes", default="1920x1080")
    ap.add_argument("--qa", action="store_true", help="prefix files with the size, skip phone page")
    ap.add_argument("--hide-fixture-banner", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sizes = [tuple(int(v) for v in s.split("x")) for s in a.sizes.split(",")]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        reports = [capture(browser, s, a.out, a.qa, a.hide_fixture_banner) for s in sizes]
        browser.close()
    print(json.dumps(reports, indent=1))


if __name__ == "__main__":
    main()
