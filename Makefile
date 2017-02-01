# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = python3 -c "import sys,sphinx;sys.exit(sphinx.main(sys.argv))"
PAPER         =
BUILDDIR      = docs/build

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) docs/source
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) source

.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  deploy     deploys to the gh-pages section of the repository"

.PHONY: clean
clean:
	rm -rf $(BUILDDIR)/*

.PHONY: html
html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)."

.PHONY: deploy
deploy:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)
	ghp-import -n $(BUILDDIR) -m "Travis documentation push"
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)."
	git push -fq https://$(TRAVIS_GH_TOKEN)@github.com/smartshark/vcsSHARK.git gh-pages
	@echo
	@echo "Push finished. The HTML pages are pushed to https://smartshark.github.io/vcsSHARK/"