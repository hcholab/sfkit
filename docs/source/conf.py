# sourcery skip: avoid-global-variables
# Configuration file for the Sphinx documentation builder.

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- Project information

project = "sfkit"
copyright = "2022, Simon Mendelsohn"
author = "Simon Mendelsohn"

release = "0.1"
version = "0.1.0"

# -- General configuration

extensions = [
    "sphinx_inline_tabs",
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinxarg.ext",
    "sphinx_copybutton",
]

copybutton_exclude = ".linenos, .gp"

autosummary_generate = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"

# -- Options for EPUB output
epub_show_urls = "footnote"

# These folders are copied to the documentation's HTML output
html_static_path = ["_static"]

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "custom.css",
]
