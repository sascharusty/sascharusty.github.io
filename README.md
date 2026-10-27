# sascharust.com

Personal site for Sascha Rust. Plain HTML, CSS and a small script, built from the Claude Design handoff. No build step: edit `index.html` and push to `main`, and GitHub Pages republishes it.

- `index.html`: all content
- `styles.css`: design tokens and layout
- `site.js`: email reveal and the article reader (the page works without it)

## Writing (from Substack)
Articles are written and published on [Substack](https://sascharust.substack.com). Once a day, the "Copy Substack posts to the site" GitHub Action (`.github/workflows/substack-sync.yml`) runs `scripts/sync_substack.py`, which copies every post into the Writing section of `index.html` in this site's design, and keeps a copy in `substack/articles.json`. Edits on Substack are picked up the same way. The Writing section and its nav link stay hidden until the first post.

- To copy a new post straight away: Actions tab, "Copy Substack posts to the site", "Run workflow".
- Don't edit the Writing section in `index.html` by hand; the next run overwrites it. Edit the post on Substack instead.
- Paid-only posts come through as Substack's preview. Subscribe buttons, polls and embeds are removed; videos become links.
- GitHub pauses scheduled actions after 60 days without any change to the repo, and emails a warning first. To restart it, open the action on the Actions tab and click "Enable workflow".

## Domain and email
- DNS for sascharust.com is hosted by Fastmail (nameservers ns1/ns2.messagingengine.com); Hover is only the registrar. Website records (four GitHub A records and the www CNAME) live in Fastmail.
- Link previews use the title and description only. To add a preview image, put a 1200×630 `og.jpg` in the repo root and add the `og:image` tags back.
