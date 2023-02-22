# autophoto

## Description

Get a photo album from your holidays in an instant!

You can either control exactly how each template is used, or just let the algorithm randomly arrange your pictures. 
The pictures order is preserved as much as possible, but not necessarily within a page, because of orientations.

The generated album is simple Latex, so you can tweak the output as you need.

## Install

### Python
```bash
python3 -m build
pipx install dist/autophoto-*.whl
```

Installation with pip (test in a separate virtual environment):
```bash
pip install -r requirements.txt
pip install dist/autophoto-*.whl
```

### Latex

Latex: xelatex/texlive full (otherwise need to change font in template)

## Usage

### Command line

Put the photos you want to turn into an album into some folder `FOLDER` following the structure detailed below.
Run the script with:

```bash
autophoto FOLDER
``` 
(or `python -m main.py FOLDER` if executed from source).
You can readily test it with the `ExampleAlbum` provided in the git repository.

A photo album is created into a newly created folder.
Since the output is random, you can run the script multiple times.

Since it outputs basic Latex, it can also be edited by hand afterwards.

### Folder structure

Your album consists of a folder with:
- A cover page (an image)
- Subfolders (or parts) `order:name:template/resegment`. The order component determines the display order in the album. A name is chosen for each part, purely for organizational purposes. To organize images in each part, we can either specify an existing template, or let the script decide. E.g. `001:The First Day:one_image` will use the `one_image` page template, whereas `001:The First Day` would choose randomly any template that has one image hole.
- Images in each subfolder `order:description.extension`. They are displayed following the order, and the description accompanies each image. E.g. `20200101_001:Happy New Year! What a beautiful day..jpg`.
LaTeX code (e.g. line break `\\`) is allowed.
- Existing templates include groups of 1-6 images, a "Chapter" including one image with a title, a "Text" including one image and a (longer) description.

## Working with Pytex/Latex Templates

List all Pytex holes and how to use them, and 'no random' option.

## TODO

- [ ] Implement remaining TODOs in code
  - [ ] better image resizing
  - [ ] option to use compile with pdflatex or even skip compilation
- [ ] Finish formatting and detailing the README
  - [ ] Detail Latex requirement
  - [ ] Explain how to work with templates
  - [ ] Explain template selection CLI option
  - [ ] Explain image resizing CLI option
- [ ] publish on PyPI 
