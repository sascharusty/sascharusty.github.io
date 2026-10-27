# sascharust.com

Personal site for Sascha Rust. Plain HTML, CSS and a small script, built from the Claude Design handoff. No build step: edit `index.html` and push to `main`, and GitHub Pages republishes it.

- `index.html`: all content
- `styles.css`: design tokens and layout
- `site.js`: email reveal and the article reader (the page works without it)

## Writing (from Substack)
Articles are written and published on [Substack](https://sascharust.substack.com). To put one on this site, send Claude the post's link in the Personal Page project. Claude runs `scripts/substack_posts.py`, which cleans the post into this site's design, saves it in `substack/articles.json` and rebuilds the Writing section of `index.html`. Each article ends with a link to the Substack original. The Writing section and its nav link stay hidden until the first post.

- Don't edit the Writing section in `index.html` by hand, because the script overwrites it.
- To change a post, edit it on Substack and send the link again. To take one down, ask Claude.
- Substack blocks automated requests from GitHub's servers, so this can't run on a schedule.

## Domain and email
- DNS for sascharust.com is hosted by Fastmail (nameservers ns1/ns2.messagingengine.com); Hover is only the registrar. Website records (four GitHub A records and the www CNAME) live in Fastmail.
- Link previews use the title and description only. To add a preview image, put a 1200×630 `og.jpg` in the repo root and add the `og:image` tags back.
