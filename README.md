# pytex

## Description

Get a photo album from your holidays in an instant!

## Usage
Put the photos you want to turn into an album into some folder FOLDER.

pipx uninstall autophoto-woolion # if already installed
python3 -m build
pipx install ./dist/autophoto_woolion-0.0.1*.whl

Otherwise use ./main.py --folder FOLDER, and voilà! (for the full list, type ./main -h or ./main.py -l)
(Later: autophoto folder)
A photo album is created into a newly created folder.
Since the output is random, you can run the script multiple times.

Since it outputs basic Latex, it can also be edited by hand afterwards.

Your album consists of a folder with:
- A cover page (an image)
- Subfolders (or parts) order:name:template/resegment. The order component determines the display order in the album. A name is chosen for each part, purely for organizational purposes. To organize images in each part, we can either specify an existing template, or let the script decide. E.g. 001:The First Day:one_image.
- Images in each subfolder order:description.extension. They are displayed following the order, and the description accompanies each image. E.g. 20200101_001:Happy New Year! What a beautiful day..jpg.
LaTeX line break \\ is allowed.
- Existing templates include groups of 1-6 images, a "Chapter" including one image with a title, a "Text" including one image and a (longer) description.

## Requirements

Latex, Python3

## TODO

- [ ] Incomplete tasks
    - [x] Adapt the script to work allow to specify if the image holders are vertical or horizontal
    - [ ] (?) Linux installation script
