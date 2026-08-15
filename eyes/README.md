# Eyes

Glowing eyes that follow the cursor. Single file, no dependencies.

Run locally:

```bash
cd eyes
python3 -m http.server 8000
```

Then open http://localhost:8000

## Note on embedding in the profile README

GitHub strips `<script>` and `<iframe>` from rendered Markdown, so this page
cannot run inside the profile README as-is. Only `<img>` survives, which means
the README version has to be an image/animated SVG generated from this design —
it can blink or glance around on a timer, but it cannot track the visitor's
cursor. This folder is the design sandbox for that.
