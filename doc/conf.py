import sys
sys.path.append("..")

from lemoncheesecake_requests.__version__ import __version__


project = 'lemoncheesecake-requests'
copyright = '2021, Nicolas Delon'
author = 'Nicolas Delon'
version = __version__
release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx"
]

autodoc_typehints = "description"
autodoc_default_options = {
    'member-order': 'bysource'
}

templates_path = ['_templates']

# This is not actually the root doc (the root doc is "index") but we need
# so that Sphinx knows about the toc
root_doc = "toc"

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_theme_options = {
    "page_width": "1150px",
    "sidebar_width": "300px",
    "fixed_sidebar": True
}
html_sidebars = {
    '**': [
        'logo.html',
        'relations.html',  # needs 'show_related': True theme option to display
        'navigation.html',
        'links.html',
        'searchbox.html',
    ]
}
html_static_path = ['_static']
html_show_sourcelink = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "lemoncheesecake": ("http://docs.lemoncheesecake.io/en/latest", None),
    "requests": ("https://docs.python-requests.org/en/latest", None)
}
