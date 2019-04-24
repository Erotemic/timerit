#!/bin/bash

init_docs(){

    REPO_NAME=$1
    REPO_NICE=$REPO_NAME
    #REPO_NICE=$2
    #Timerit

    REPO_DPATH=$HOME/code/$REPO_NAME

    PKG_DPATH=$REPO_DPATH/$REPO_NAME


    echo "REPO_DPATH = $REPO_DPATH"
    echo "PKG_DPATH = $PKG_DPATH"

    echo "MAKING DOCS"


    echo "$(codeblock "
    sphinx
    -e git://github.com/snide/sphinx_rtd_theme.git#egg=sphinx_rtd_theme
    ")" >  $REPO_DPATH/docs/requirements.txt
    pip install -r $REPO_DPATH/docs/requirements.txt


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


    # Now populate $REPO_DPATH/docs/source/index.rst and $REPO_DPATH/docs/source/conf.py 


    # Make conf.py use the read-the-docs theme
    sed -i "s/html_theme = 'alabaster'/import sphinx_rtd_theme  # NOQA\nhtml_theme = 'sphinx_rtd_theme'\nhtml_theme_path = [sphinx_rtd_theme.get_html_theme_path()]/g" $REPO_DPATH/docs/source/conf.py

    sed -i "s/version = ''/import $REPO_NAME\nversion = '.'.join($REPO_NAME.__version__.split('.')[0:2])/g" $REPO_DPATH/docs/source/conf.py


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

    :github_url: https://github.com/Erotemic/ubelt

    reponice documentation
    ======================

    REPO_NICE=$REPO_NICE

    You have to populate the index page yourself 

    TODO: have someone who understands this write docs


    .. The __init__ files contains the top-level documentation overview
    .. automodule:: $REPO_NAME.__init__
       :show-inheritance:

    .. commented out
    .. :members:
    .. :undoc-members:


    .. toctree::
       :maxdepth: 8
       :caption: API

       modules
        
    ")" > $REPO_DPATH/docs/source/index.rst



    cd $REPO_DPATH/docs
    sphinx-apidoc -f -o $REPO_DPATH/docs/source $PKG_DPATH --separate

    cd $REPO_DPATH/docs
    make html

    google-chrome build/html/index.html



    echo "$(codeblock "
    # .readthedocs.yml
    # Read the Docs configuration file
    # See https://docs.readthedocs.io/en/stable/config-file/v2.html for details

    # Required
    version: 2

    # Build documentation in the docs/ directory with Sphinx
    sphinx:
      configuration: docs/conf.py

    # Optionally build your docs in additional formats such as PDF and ePub
    formats: all

    # Optionally set the version of Python and requirements required to build your docs
    python:
      version: 3.7
      install:
        requirements:
           - docs/requirements.txt
        extra_requirements:
           - docs
        

    ")" > $REPO_DPATH/.readthedocs.yml

}


dev_main(){
    source 
    init_docs progiter
}

init_docs $1
