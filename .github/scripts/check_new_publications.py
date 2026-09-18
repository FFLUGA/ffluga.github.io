"""
Checks Francisco Fernandez-Lima's ORCID record for publications that aren't
yet listed on docs/publications.html, and inserts draft entries for any new
ones. Run by .github/workflows/check-new-publications.yml.

"New" = an ORCID work whose DOI (or URL, or normalized title as a last
resort) doesn't already appear anywhere in publications.html. There's no
separate manifest file to keep in sync -- the current HTML is the source of
truth for what's "known".
"""

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ORCID_ID = "0000-0002-1283-4390"
ORCID_WORKS_URL = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUBLICATIONS_HTML = os.path.join(REPO_ROOT, "docs", "publications.html")
USER_AGENT = "fernandez-lima-lab-publications-bot/1.0 (+https://github.com/FFLUGA/ffluga.github.io)"


def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_title(title):
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def load_known_identifiers(publications_html_path):
    content = open(publications_html_path, encoding="utf-8").read()
    dois = set(m.lower() for m in re.findall(r'doi\.org/([^"?\s]+)', content, re.I))
    links = set(re.findall(r'href="(https://[^"]+)"', content))
    titles = set(normalize_title(html.unescape(t)) for t in re.findall(r"<h3><a[^>]*>([^<]+)</a></h3>", content))
    return dois, links, titles


def get_orcid_works():
    data = fetch_json(ORCID_WORKS_URL)
    works = []
    for group in data.get("group", []):
        summaries = group.get("work-summary", [])
        if not summaries:
            continue
        w = summaries[0]
        title = ((w.get("title") or {}).get("title") or {}).get("value", "")
        year = (((w.get("publication-date") or {}).get("year")) or {}).get("value")
        ext_ids = ((w.get("external-ids") or {}).get("external-id") or [])
        doi = None
        for e in ext_ids:
            if (e.get("external-id-type") or "").lower() == "doi":
                doi = e.get("external-id-value")
                break
        url = (w.get("url") or {}).get("value")
        journal = (w.get("journal-title") or {}).get("value")
        works.append(
            {
                "put_code": w.get("put-code"),
                "title": title,
                "year": year,
                "doi": doi,
                "url": url,
                "journal": journal,
            }
        )
    return works


def enrich_with_crossref(doi):
    try:
        data = fetch_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")
    except Exception:
        return {}
    msg = data.get("message", {})
    authors = msg.get("author") or []
    names = [f"{a.get('given', '').strip()} {a.get('family', '').strip()}".strip() for a in authors[:6]]
    names = [n for n in names if n]
    author_str = ", ".join(names)
    if len(authors) > 6:
        author_str += ", et al."
    container = (msg.get("container-title") or [None])[0]
    return {
        "authors": author_str,
        "journal": container,
        "volume": msg.get("volume"),
        "issue": msg.get("issue"),
        "page": msg.get("page"),
    }


def build_snippet(work, meta):
    year = work["year"] or "TODO-YEAR"
    title = html.escape(work["title"] or "TODO: title")
    authors = html.escape(meta.get("authors") or "TODO: authors (check the paper)")
    journal = meta.get("journal") or work["journal"] or "TODO: journal"
    venue_bits = [journal]
    vol_issue = ""
    if meta.get("volume"):
        vol_issue = str(meta["volume"])
        if meta.get("issue"):
            vol_issue += f"({meta['issue']})"
    if vol_issue:
        venue_bits.append(vol_issue)
    if meta.get("page"):
        venue_bits.append(str(meta["page"]))
    venue = html.escape(", ".join(b for b in venue_bits if b)) + f" &middot; {year}"

    if work["doi"]:
        link = f"https://doi.org/{work['doi']}"
    elif work["url"]:
        link = work["url"]
    else:
        link = "https://scholar.google.com/scholar?q=" + urllib.parse.quote(work["title"] or "")

    return f"""        <!-- TODO (new from ORCID): set data-cats to the correct research-area id(s) and add matching .tag span(s) below, then remove this comment -->
        <li class="pub-item" data-cats="">
          <span class="pub-year">{year}</span>
          <h3><a href="{link}" target="_blank" rel="noopener">{title}</a></h3>
          <p class="pub-authors">{authors}</p>
          <p class="pub-venue"><em>{venue}</em></p>
          <div class="pub-tags">
            <!-- TODO: e.g. <span class="tag tag-protein"><span class="tag-dot"></span>Protein-Protein &amp; Protein-DNA</span> -->
          </div>
        </li>
"""


def write_github_output(**kwargs):
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        for key, value in kwargs.items():
            f.write(f"{key}={value}\n")


def main():
    if not os.path.isfile(PUBLICATIONS_HTML):
        print(f"Could not find {PUBLICATIONS_HTML}", file=sys.stderr)
        sys.exit(1)

    known_dois, known_links, known_titles = load_known_identifiers(PUBLICATIONS_HTML)

    try:
        works = get_orcid_works()
    except urllib.error.URLError as e:
        print(f"Failed to reach ORCID: {e}", file=sys.stderr)
        sys.exit(1)

    new_works = []
    for w in works:
        doi_norm = (w["doi"] or "").lower().strip()
        if doi_norm and doi_norm in known_dois:
            continue
        if w["url"] and w["url"] in known_links:
            continue
        if normalize_title(w["title"]) in known_titles:
            continue
        new_works.append(w)

    if not new_works:
        print("No new publications found.")
        write_github_output(has_new="false")
        return

    snippets = []
    for w in new_works:
        meta = enrich_with_crossref(w["doi"]) if w["doi"] else {}
        snippets.append(build_snippet(w, meta))

    content = open(PUBLICATIONS_HTML, encoding="utf-8").read()
    marker = '<ul class="pub-list">\n'
    idx = content.find(marker)
    if idx == -1:
        print("Could not find <ul class=\"pub-list\"> marker in publications.html", file=sys.stderr)
        sys.exit(1)
    insert_at = idx + len(marker)
    content = content[:insert_at] + "".join(snippets) + content[insert_at:]

    m = re.search(r'(data-filter="all">All <span class="filter-count">\()(\d+)(\)</span>)', content)
    if m:
        new_count = int(m.group(2)) + len(new_works)
        content = content[: m.start(2)] + str(new_count) + content[m.end(2) :]

    with open(PUBLICATIONS_HTML, "w", encoding="utf-8") as f:
        f.write(content)

    titles_joined = "; ".join((w["title"] or "(untitled)") for w in new_works)
    titles_joined = titles_joined.replace("\n", " ")[:900]

    print(f"Added {len(new_works)} new publication(s):")
    for w in new_works:
        print(f"  - {w['title']} ({w['year']})")

    write_github_output(has_new="true", count=len(new_works), titles=titles_joined)


if __name__ == "__main__":
    main()
