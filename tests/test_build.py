"""Run: python3 -m unittest discover -s tests   (from the project root)."""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build  # noqa: E402


class MarkdownSafety(unittest.TestCase):
    def test_raw_html_escaped(self):
        out = build.render_markdown("<script>alert(1)</script> and <img src=x onerror=alert(1)>")
        self.assertNotIn("<script", out)
        self.assertNotIn("<img", out)
        self.assertIn("&lt;script&gt;", out)

    def test_unsafe_links_dropped(self):
        out = build.render_inline("[x](javascript:alert(1)) [y](data:text/html,hi) [z](//evil.example/a)")
        self.assertNotIn("href", out)

    def test_safe_links_kept(self):
        out = build.render_inline("[a](https://example.org/?q=1&r=2) [b](../) [c](#top)")
        self.assertIn('href="https://example.org/?q=1&amp;r=2"', out)
        self.assertIn('href="../"', out)
        self.assertIn('href="#top"', out)

    def test_code_block_escaped(self):
        out = build.render_markdown("```html\n<script>x</script>\n```")
        self.assertIn("&lt;script&gt;x&lt;/script&gt;", out)
        self.assertNotIn("<script", out)

    def test_headings_lists(self):
        out = build.render_markdown("# T\n\n## S\n\n- a\n- b\n\n1. c\n2. d")
        self.assertIn("<h2", out)
        self.assertIn("<ul><li>a</li><li>b</li></ul>", out)
        self.assertIn("<ol><li>c</li><li>d</li></ol>", out)


class FullBuild(unittest.TestCase):
    def test_default_build_has_no_invented_articles(self):
        with tempfile.TemporaryDirectory() as d:
            site, out, problems, _, count = build.build(out=Path(d) / "dist")
            self.assertEqual(problems, [])
            self.assertEqual(site.articles, [])
            self.assertFalse((out / "sitemap.xml").exists())
            self.assertFalse((out / "robots.txt").exists())
            home = (out / "index.html").read_text()
            self.assertNotIn("canonical", home)
            self.assertIn("Working note", home)
            self.assertNotIn("datePublished", home)

    def test_articles_and_base_url(self):
        with tempfile.TemporaryDirectory() as d:
            site, out, problems, _, count = build.build(
                articles_dir=HERE / "fixtures" / "articles", base_url="https://example.test/site", out=Path(d) / "dist")
            self.assertEqual(problems, [])
            self.assertEqual(len(site.articles), 2)
            page = (out / "writing" / "fixture-hostile" / "index.html").read_text()
            self.assertNotIn("<script>alert", page)
            self.assertIn("datePublished", page)
            self.assertIn("https://example.test/site/writing/fixture-hostile/", (out / "sitemap.xml").read_text())
            plain = (out / "writing" / "fixture-plain" / "index.html").read_text()
            self.assertNotIn("datePublished", plain)
            self.assertIn("<title>FIXTURE ONLY plain article | Faheem Dehalvi</title>", plain)

    def test_refuses_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "keep.txt").write_text("x")
            with self.assertRaises(build.BuildError):
                build.build(out=Path(d))


if __name__ == "__main__":
    unittest.main()
