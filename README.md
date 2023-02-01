# pytex

## Description

Get a photo album from your holidays in an instant!

You can either control exactly how each template is used, or just let the algorithm
randomly arrange your pictures. 
The pictures order is preserved as much as possible, but not necessarily within a page,
because of orientations.

The album generated is simple Latex, so you can tweak the output as you need.

## Usage
Put the photos you want to turn into an album into some folder FOLDER.

pipx uninstall autophoto-woolion # if already installed
python3 -m build # to create the tar.gz
pipx install ./dist/autophoto_woolion-*.whl

Installation with pip (test in a separate virtual environment): 
pip install autophoto_woolion-0.0.1.tar.gz

`autophoto FOLDER` 
(or ./main.py -f FOLDER)
You can readily test it with the `ExampleAlbum` provided.

A photo album is created into a newly created folder.
Since the output is random, you can run the script multiple times.

Since it outputs basic Latex, it can also be edited by hand afterwards.

Your album consists of a folder with:
- A cover page (an image)
- Subfolders (or parts) order:name:template/resegment. The order component determines the display order in the album. A name is chosen for each part, purely for organizational purposes. To organize images in each part, we can either specify an existing template, or let the script decide. E.g. 001:The First Day:one_image.
- Images in each subfolder order:description.extension. They are displayed following the order, and the description accompanies each image. E.g. 20200101_001:Happy New Year! What a beautiful day..jpg.
LaTeX line break `\\` is allowed.
- Existing templates include groups of 1-6 images, a "Chapter" including one image with a title, a "Text" including one image and a (longer) description.

## Requirements

Latex: xelatex/texlive full (otherwise need to change font in template)

## Working with Pytex/Latex

List all Pytex holes and how to use them.

## TODO

- [ ] Implement remaining TODOs in code
- [ ] gitignore
- [ ] Finish formatting and detailing the README
- [ ] publish on PyPI 
