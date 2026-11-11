---
title: FIXTURE ONLY <script>alert(1)</script> hostile markdown
slug: fixture-hostile
published: 2026-01-02
---

# FIXTURE ONLY <script>alert(1)</script> hostile markdown

Raw <img src=x onerror=alert(1)> and <script>alert(2)</script> must be escaped.

[bad link](javascript:alert(3)) and [data link](data:text/html;base64,AAAA) and [ok link](https://example.org/a?b=1&c=2) and [rel](../)

## Heading with `code` & ampersand

- item **bold** and *italic*
- item two
  continued line

1. first
2. second

```html
<script>alert(4)</script>
```

> quote with <b>tag</b>
