# sascharust.com

Personal site for Sascha Rust. Plain HTML, CSS and a small script, built from the Claude Design handoff. No build step: edit `index.html` and push to `main`, and GitHub Pages republishes it.

- `index.html`: all content
- `styles.css`: design tokens and layout
- `site.js`: email reveal and the article reader (the page works without it)

## Adding writing
The Writing section is commented out in `index.html` until there is a real article. Instructions are in the comment.

## Before launch on sascharust.com
1. Add `og.jpg` (1200×630) to the repo root.
2. Point the domain at GitHub Pages and add it under Settings → Pages → Custom domain.
3. Set SPF, DKIM and DMARC (`p=reject`) for sascharust.com.
