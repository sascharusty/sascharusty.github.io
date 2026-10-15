# sascharust.com

Personal site for Sascha Rust. Plain HTML, CSS and a small script, built from the Claude Design handoff. No build step: edit `index.html` and push to `main`, and GitHub Pages republishes it.

- `index.html`: all content
- `styles.css`: design tokens and layout
- `site.js`: email reveal and the article reader (the page works without it)

## Adding writing
The Writing section is commented out in `index.html` until there is a real article. Instructions are in the comment.

## Domain and email
- DNS for sascharust.com is hosted by Fastmail (nameservers ns1/ns2.messagingengine.com); Hover is only the registrar. Website records (four GitHub A records and the www CNAME) live in Fastmail.
- Link previews use the title and description only. To add a preview image, put a 1200×630 `og.jpg` in the repo root and add the `og:image` tags back.
