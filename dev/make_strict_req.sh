#!/bin/bash
__doc__="""
Make a strict version of requirements

./dev/make_strict_req.sh
"""
mkdir -p requirements-strict
sed 's/>=/==/' requirements/runtime.txt > requirements-strict/runtime.txt
sed 's/>=/==/' requirements/docs.txt > requirements-strict/docs.txt
sed 's/>=/==/' requirements/tests.txt > requirements-strict/tests.txt
#sed 's/>=/==/' requirements/headless.txt > requirements-strict/headless.txt  # opencv issues
#sed 's/>=/==/' requirements/graphics.txt > requirements-strict/graphics.txt  # opencv issues
sed 's/requirements/requirements-strict/' requirements.txt > requirements-strict.txt
