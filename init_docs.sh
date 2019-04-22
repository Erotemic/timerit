
REPO_NAME=timerit
REPO_DPATH=$HOME/code/$REPO_NAME
PKG_DPATH=$REPO_DPATH/$REPO_NAME


echo "MAKING DOCS"
rm -rf $REPO_DPATH/docs
mkdir -p $REPO_DPATH/docs
sphinx-quickstart -q --sep \
    --project=$REPO_NAME \
    --author="Jon Crall" \
    --ext-autodoc \
    --ext-viewcode \
    --ext-intersphinx \
    --ext-todo \
    --extensions=sphinx.ext.napoleon,sphinx.ext.autosummary \
    $REPO_DPATH/docs


echo "$(codeblock "
sphinx
-e git://github.com/snide/sphinx_rtd_theme.git#egg=sphinx_rtd_theme
")" >  $REPO_DPATH/docs/requirements.txt


pip install -r $REPO_DPATH/docs/requirements.txt


# Now populate $REPO_DPATH/docs/source/index.rst and $REPO_DPATH/docs/source/conf.py 


# Make conf.py use the read-the-docs theme
sed -i "s/html_theme = 'alabaster'/import sphinx_rtd_theme  # NOQA\nhtml_theme = 'sphinx_rtd_theme'\nhtml_theme_path = [sphinx_rtd_theme.get_html_theme_path()]/g" $REPO_DPATH/docs/source/conf.py

sed -i "s/version = ''/import $REPO_NAME\nversion = '.'.join($REPO_NAME.__version__.split('.')[0:2])/g" $REPO_DPATH/docs/source/conf.py

sphinx-apidoc -f -o $REPO_DPATH/docs/source $PKG_DPATH --separate
echo "REPO_DPATH = $REPO_DPATH"
echo "PKG_DPATH = $PKG_DPATH"


echo "$(codeblock "
todo_include_todos = True
napoleon_google_docstring = True
napoleon_use_param = False
napoleon_use_ivar = True
autodoc_inherit_docstrings = False
autodoc_member_order = 'bysource'

html_theme_options = {
    'collapse_navigation': False,
    'display_version': True,
    # 'logo_only': True,
}
    
")" >> $REPO_DPATH/docs/source/conf.py


echo "$(codeblock "

You have to populate the index page yourself 

TODO: have someone who understands this write docs
    
")" >> $REPO_DPATH/docs/source/index.rst


cd $REPO_DPATH/docs
make html

google-chrome build/html/index.html
