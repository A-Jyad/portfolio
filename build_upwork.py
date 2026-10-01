"""Build the Upwork-safe copy of the portfolio into upwork/.

Upwork doesn't allow sharing direct contact details (email, LinkedIn, phone,
messaging apps) before a contract starts. This script copies index.html and the
case studies into upwork/, swapping every <!-- private:NAME --> block for the
Upwork-only version below and rewriting relative paths for the deeper folder.

Run it after editing index.html or anything in projects/:

    python build_upwork.py
"""

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "upwork"

UPWORK_PROFILE = "https://www.upwork.com/freelancers/ahmedj136"

REPLACEMENTS = {
    "sidebar-contacts": f"""<ul class="contacts-list">

          <li class="contact-item">
            <div class="icon-box">
              <ion-icon name="briefcase-outline"></ion-icon>
            </div>
            <div class="contact-info">
              <p class="contact-title">Upwork</p>
              <a href="{UPWORK_PROFILE}" class="contact-link" target="_blank">ahmedj136</a>
            </div>
          </li>

        </ul>""",

    "contact-options": f"""<section class="contact-options">

          <p class="contact-intro">
            Have a data problem worth solving? Send me a message on Upwork and tell me about it. I usually reply
            within a day.
          </p>

          <ul class="contact-options-list">

            <li>
              <a href="{UPWORK_PROFILE}" class="contact-option" target="_blank" rel="noopener">
                <div class="icon-box">
                  <ion-icon name="briefcase-outline"></ion-icon>
                </div>
                <div class="contact-option-text">
                  <p class="contact-option-title">Upwork</p>
                  <p class="contact-option-handle">Message me on Upwork</p>
                </div>
                <ion-icon class="contact-option-arrow" name="arrow-forward-outline"></ion-icon>
              </a>
            </li>

          </ul>

        </section>""",
}

# anything matching these must not survive into the Upwork build
FORBIDDEN = [
    r"mailto:", r"@gmail\.com", r"linkedin\.com", r"github\.com",
    r"wa\.me", r"t\.me/", r"logo-whatsapp", r"telegram",
]

BLOCK = re.compile(
    r"<!-- private:(?P<name>[\w-]+)[^>]*-->\s*(?P<body>.*?)\s*<!-- /private:(?P=name) -->",
    re.DOTALL,
)


def strip_private(html, source):
    found = set()

    def swap(match):
        name = match.group("name")
        if name not in REPLACEMENTS:
            raise SystemExit(f"{source}: no Upwork replacement defined for private block '{name}'")
        found.add(name)
        return REPLACEMENTS[name]

    html = BLOCK.sub(swap, html)
    if "<!-- private:" in html:
        raise SystemExit(f"{source}: unclosed private block")
    return html, found


def check_clean(html, source):
    for pattern in FORBIDDEN:
        if re.search(pattern, html, re.IGNORECASE):
            raise SystemExit(f"{source}: contact detail matching '{pattern}' leaked into the Upwork build")


def write(path, html):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8", newline="")


def build_index():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    html, found = strip_private(html, "index.html")
    missing = set(REPLACEMENTS) - found
    if missing:
        raise SystemExit(f"index.html: private markers missing for {', '.join(sorted(missing))}")

    html = html.replace('"./assets/', '"../assets/')
    html = html.replace("https://a-jyad.github.io/portfolio/\"", "https://a-jyad.github.io/portfolio/upwork/\"")
    # keep the Upwork copy out of search results
    html = html.replace("<title>", '<meta name="robots" content="noindex">\n  <title>', 1)

    check_clean(html, "upwork/index.html")
    write(OUT / "index.html", html)


def build_projects():
    for page in sorted((ROOT / "projects").glob("*.html")):
        html = page.read_text(encoding="utf-8")
        html, _ = strip_private(html, f"projects/{page.name}")
        # ../index.html stays as-is: from upwork/projects/ it resolves to upwork/index.html
        html = html.replace('"../assets/', '"../../assets/')
        html = html.replace("<title>", '<meta name="robots" content="noindex">\n  <title>', 1)

        check_clean(html, f"upwork/projects/{page.name}")
        write(OUT / "projects" / page.name, html)


if __name__ == "__main__":
    if OUT.exists():
        shutil.rmtree(OUT)
    build_index()
    build_projects()
    print(f"Built Upwork copy in {OUT.relative_to(ROOT)}/")
