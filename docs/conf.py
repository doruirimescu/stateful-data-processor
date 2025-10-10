# This file is execfile()d with the current directory set to its containing dir.
#
# See https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import shutil

# -- Path setup --------------------------------------------------------------
__location__ = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(__location__, "../src"))

# -- Run sphinx-apidoc -------------------------------------------------------
try:  # for Sphinx >= 1.7
    from sphinx.ext import apidoc
except ImportError:
    from sphinx import apidoc

output_dir = os.path.join(__location__, "api")
module_dir = os.path.join(__location__, "../src/stateful_data_processor")
try:
    shutil.rmtree(output_dir)
except FileNotFoundError:
    pass

try:
    import sphinx

    cmd_line = f"sphinx-apidoc --implicit-namespaces -f -o {output_dir} {module_dir}"
    args = cmd_line.split(" ")
    if tuple(sphinx.__version__.split(".")) >= ("1", "7"):
        args = args[1:]
    apidoc.main(args)
except Exception as e:
    print("Running `sphinx-apidoc` failed!\n{}".format(e))

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.ifconfig",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    # --- Added for Markdown (MyST) ---
    "myst_parser",
]

templates_path = ["_templates"]

# --- Changed: allow both .rst and .md sources ---
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The master toctree document.
master_doc = "index"

# Project info
project = "stateful-data-processor"
copyright = "2024, Doru Irimescu"

# Versioning
try:
    from stateful_data_processor import __version__ as version
except ImportError:
    version = ""
if not version or version.lower() == "unknown":
    version = os.getenv("READTHEDOCS_VERSION", "unknown")
release = version

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".venv"]

pygments_style = "sphinx"

# Keep TODOs visible in builds (adjust as you like)
todo_emit_warnings = True

# --- Nice-to-have MyST options (safe defaults) ---
myst_enable_extensions = [
    "colon_fence",   # ::: fenced blocks
    "linkify",       # autolink bare URLs
    "deflist",
    "attrs",
]
# Generate stable anchors for H1-H3 headings in Markdown
myst_heading_anchors = 3

# -- Options for HTML output -------------------------------------------------
html_theme = "alabaster"
html_theme_options = {
    "sidebar_width": "300px",
    "page_width": "1200px",
}
html_static_path = ["_static"]
htmlhelp_basename = "stateful-data-processor-doc"

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {}
latex_documents = [
    ("index", "user_guide.tex", "stateful-data-processor Documentation", "Doru Irimescu", "manual")
]

# -- External mapping --------------------------------------------------------
python_version = ".".join(map(str, sys.version_info[0:2]))
intersphinx_mapping = {
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
    "python": ("https://docs.python.org/" + python_version, None),
    "matplotlib": ("https://matplotlib.org", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "sklearn": ("https://scikit-learn.org/stable", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    "setuptools": ("https://setuptools.pypa.io/en/stable/", None),
    "pyscaffold": ("https://pyscaffold.org/en/stable", None),
}

print(f"loading configurations for {project} {version} ...", file=sys.stderr)
