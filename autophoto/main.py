#!/usr/bin/env python3

import sys
import os
from shutil import copy
import re
import random
import datetime
import subprocess
import configargparse as argparse
import constraint

WARNINGS = []

DEFAULT_TEMPLATE_FOLDER = './Latex'
DEFAULT_TEMPLATE = 'Default'
DEFAULT_MAIN_NAME = 'main.pytex'
OUTPUT_MAIN_NAME = 'main.tex'

PYTEX_ISPAGE = '(%%PAGE)'
PYTEX_NORANDOM = '(%%NORANDOM)'
PYTEX_ISMAIN = '(%%MAIN)'
PYTEX_ISCOVER = '(%%COVER)'
PYTEX_BLANK = '(%!!.*!!%)'
PYTEX_OPT_START = '(%%!-)'
PYTEX_OPT_CAPTION = '(%--%)'
PYTEX_PAGES = '(%%%pages%%%)'
PYTEX_COV = '(%%%cover%%%)'

PYTEX_COVER = {'name': 'cover.pytex', 'marker': PYTEX_ISCOVER}


def orientation(x, y):
    # this drives how much we allow a vertical to be used in a square or the opposite
    tolerance = .2  # TODO: make tolerance configurable
    return (abs(x / y - 1) < tolerance and 'a') or (x > y and 'h') or 'v'


def opposite(orientation):
    return "v" if orientation == "h" else "h" if orientation == "v" else "a"


def cost_reorder(target, input, order):
    units = sum(abs(i - order[i]) ** 2 for i in range(len(order)))
    hundreds = sum(10 * (0 if target[i] == input[order[i]] else 1) for i in range(len(order)))
    return hundreds + units


def compatible_orientations(target, input):
    result = len(target) == len(input)
    for t, o in zip(target, input):
        result &= (t == "a" or o == "a" or t == o)
    return result


def get_reorientations(target, input):
    problem = constraint.Problem()
    indices = range(len(target))
    domain = range(len(target))
    problem.addVariables(indices, domain)
    problem.addConstraint(constraint.AllDifferentConstraint())
    for i, t in enumerate(target):
        if t == "h":
            problem.addConstraint(lambda i: input[i] != "v", [i])
        if t == "v":
            problem.addConstraint(lambda i: input[i] != "h", [i])
    return problem.getSolutions()


def orientation_reorder(target, input):
    solutions = get_reorientations(target, input)
    if not solutions:  # we are probably in lax mode, forced by manual template choice
        solutions = [{i: i for i in range(len(target))}]  # we simply don't reorder
    sol = min((s for s in solutions), key=lambda s: cost_reorder(target, input, s))
    return [sol[i] for i in range(len(target))]


class Template:
    def __init__(self, name, pytex):
        self.name = name
        self.pytex = pytex
        self.random = not re.search(PYTEX_NORANDOM, pytex)

    @staticmethod
    def is_pytex_template(pattern, filepath):
        try:
            assert (filepath.endswith(".pytex"))
            content = open(filepath).read()
            assert (re.match(pattern, content.split()[0]))
            name = os.path.splitext(os.path.basename(filepath))[0]
            return name, content
        except Exception:
            return False

    @staticmethod
    def load(folder):
        raise NotImplementedError


class TemplatePage(Template):
    def __init__(self, *args, **kwargs):
        super(TemplatePage, self).__init__(*args, **kwargs)
        self.photos_memos = None

    @staticmethod
    def is_page_template(filepath):
        name_content = Template.is_pytex_template(PYTEX_ISPAGE, filepath)
        if name_content:
            return TemplatePage(name_content[0], name_content[1])
        else:
            # if os.path.basename(filepath) != DEFAULT_MAIN_NAME and not os.path.isdir(filepath):
            #     print("Warning: {} is not a page template".format(filepath))
            return False

    @staticmethod
    def load(folder):
        list_content = []
        for file in [f for f in os.listdir(folder) if f.endswith('pytex')]:
            file_path = os.path.join(folder, file)
            content = TemplatePage.is_page_template(file_path)
            if content:
                list_content.append(content)
        return list_content

    @staticmethod
    def has_special(folder, special):
        return special['name'] in os.listdir(folder)

    @staticmethod
    def load_special(folder, special):
        name_content = Template.is_pytex_template(special['marker'], os.path.join(folder, special['name']))
        return TemplatePage(name_content[0], name_content[1])

    def photos_in_page(self):
        if not self.photos_memos:
            matches = re.findall(PYTEX_BLANK, self.pytex)
            result = []
            for match in matches:
                try:
                    x, y = [int(m) for m in match[3: -3].split(',')]
                    result.append(orientation(x, y))
                except:  # we cannot parse the dimension info; in that case let's go for 'any'
                    result.append('a')
            self.photos_memos = result
        return  self.photos_memos


class TemplateMain(Template):
    @staticmethod
    def is_main_template(filepath):
        name_content = Template.is_pytex_template(PYTEX_ISMAIN, filepath)
        if name_content:
            return TemplateMain(name_content[0], name_content[1])
        else:
            return False

    @staticmethod
    def load(folder):
        if DEFAULT_MAIN_NAME in os.listdir(folder):
            dir_content = [os.path.join(folder, f) for f in os.listdir(folder)]
            files = [f for f in dir_content if os.path.isfile(f) and not f.endswith('pytex')]
            return TemplateMain.is_main_template(os.path.join(folder, DEFAULT_MAIN_NAME)), files
        else:
            raise Exception("Template is missing a {} file".format(DEFAULT_MAIN_NAME))


class DocumentMain:
    def __init__(self, template_main, pages, output_root, files, cover):
        self.pages = pages
        self.output_root = output_root
        self.template_main = template_main
        self.files = files
        self.cover = cover

    @property
    def compiled_tex(self):
        tex_pages = [r"    \\input{" + page.page_tex() + "}" for page in self.pages]
        tex_code = "\n".join(tex_pages)
        compiled = re.sub(PYTEX_PAGES, tex_code, self.template_main.pytex)
        if self.cover:
            tex_code = r"    \\input{" + self.cover[-1].page_tex() + "}"
            compiled = re.sub(PYTEX_COV, tex_code, compiled)
        return compiled

    def write_to_disk(self):
        path = os.path.join(self.output_root, self.template_main.name + ".tex")
        f = open(path, 'w')
        f.write(self.compiled_tex)
        f.close()

        for file in self.files:
            copy(file, self.output_root)


class DocumentPage:
    """Contains an image set, a matching template and a page number"""
    def __init__(self, im_set, page_templates, page_number, output_root, options=None):
        self.im_set = im_set
        self.page_number = page_number
        self.output_root = output_root
        self.options = options or {}
        self.page_template = self.select_page_template(im_set, page_templates)

    @property
    def page_folder(self):
        return "page" + str(self.page_number)

    @property
    def compiled_tex(self):
        return self.pytex_to_tex()

    def _image_name_simplified(self, im):
        basename = os.path.basename(im.filename)
        simplified = re.sub('[^a-zA-Z0-9\.]', '', basename)
        name, extension = os.path.splitext(simplified)
        # Latex does not support webp or other image formats easily (gif, ...)
        # convert will take care of it
        if extension.lower() not in ["jpeg", "jpg"]:
            simplified = ".".join([name, "jpg"])
        return simplified

    def _image_path(self, im):
        return os.path.join(self.output_root, self.page_folder, self._image_name_simplified(im))

    def _page_path(self):
        return os.path.join(self.output_root, self.page_tex()) + ".tex"

    def page_tex(self):
        return os.path.join(self.page_folder, self.page_template.name)

    def write_to_disk(self):
        create_folder(self.page_folder, self.output_root)
        quality = "-quality 75%"  # TODO: configure with CLI option
        args = [quality, "-auto-orient", "-strip"]
        for im in self.im_set:
            # TODO: configure how and when to resize in command line arguments
            resize = im.resize_argument()
            command_base = " ".join(["convert"] + args + [resize])
            command = "%s %s %s" % (command_base, shellify_filepath(im.filename), self._image_path(im))
            subprocess.check_call(command, shell=True)
        f = open(self._page_path(), 'w')
        f.write(self.compiled_tex)
        f.close()

    def select_page_template(self, im_set, page_templates):
        name = self.options.get("template")
        if name:
            template = next((t for t in page_templates if t.name == name), None)
            if not template:
                raise Exception(f"Template not found: {name}")
        else:
            orientations = image_orientations(im_set)
            possible_pages = [p for p in page_templates if p.random and sets_compatible(orientations, p.photos_in_page())]
            if not possible_pages:
                WARNINGS.append(f"Warning: using lax mode for the following images: {[im.filename for im in im_set]}")
                possible_pages = [p for p in page_templates if p.random and sets_compatible(orientations, p.photos_in_page(), lax=True)]
            template = random.choice(possible_pages)
        if len(template.photos_in_page()) != len(im_set):
            WARNINGS.append(f"Warning: inconsistent number of images in "
                            f"template {template.name}, with {len(template.photos_in_page())} slots"
                            f"for images {[im.filename for im in im_set]}")
        return template

    def pytex_to_tex(self):
        image_paths = []
        captions = []

        target = self.page_template.photos_in_page()
        im_os = image_orientations(self.im_set)
        if not compatible_orientations(target, im_os):
            new_order = orientation_reorder(target, im_os)
            ordered_im_set = [self.im_set[i] for i in new_order]
        else:
            ordered_im_set = [im for im in self.im_set]
        for im in ordered_im_set:
            basename = self._image_name_simplified(im)
            filepath = os.path.join(self.page_folder, basename)
            options = parse_options_file(os.path.splitext(os.path.basename(im.filename))[0])
            captions.append(options.get('name', PYTEX_OPT_CAPTION))
            image_paths.append(filepath)
        s_img = re.sub(
            PYTEX_BLANK,
            lambda match: image_paths.pop(0),
            self.page_template.pytex
        )
        s_img_capt = re.sub(
            PYTEX_OPT_CAPTION,
            lambda match: captions.pop(0),
            s_img
        )
        return "\n".join((s if "%-" in s else s.replace("%%!-", "") for s in s_img_capt.splitlines()))


def shellify_filepath(filepath):
    result = filepath.replace("\\", "\\\\")
    for char in " !()'`;":
        result = result.replace(char, "\\" + char)
    return result


def is_image(filepath):
    try:
        command = f'convert -auto-orient {shellify_filepath(filepath)} info:'
        output = subprocess.check_output(command, shell=True)
        size = re.search(" \d+x\d+ ", output.decode()).group().split("x")
        return Img(filepath, width=int(size[0]), height=int(size[1]))
    except Exception:
        if not os.path.isdir(filepath):
            print("Warning: " + filepath + " cannot be opened as an image.")
        return False


class Img:
    def __init__(self, filename, width, height):
        self.filename = filename
        self.width = width
        self.height = height
        self.orientation_memo = None

    def resize_argument(self):
        # let's work with 1920x1080 as a base # TODO: configure with CLI option
        w = self.width / 2000
        h = self.height / 1000
        q = max(w, h)
        r = ""
        if q > .5:
            r = "-resize 50%"
        if q > 1:
            r = "-resize 2000x"
        return r

    @property
    def orientation(self):
        if not self.orientation_memo:
            self.orientation_memo = orientation(self.width, self.height)
        return self.orientation_memo


def image_orientations(im_set):
    return [im.orientation for im in im_set]


# FOLDER

def load_files_in_folder(root_folder, file_predicate):
    list_content = []
    for folder in sorted(f for f in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, f))):
        new_list = []
        list_content.append(new_list)
        for file in sorted(os.listdir(os.path.join(root_folder, folder))):
            file_path = os.path.join(root_folder, folder, file)
            content = file_predicate(file_path)
            if content:
                new_list.append(content)
    return list_content


def load_photos_in_folder(folder):
    return load_files_in_folder(folder, is_image)


FOLDER_OPTIONS = ['name', 'template_or_resegment']  # first is numbering
FILE_OPTIONS = ['name']

def parse_options_parametrised(name, option_list):
    args = name.split(':')[1:]
    options = dict(zip(option_list, args))
    return options


def parse_options_folder(name):
    options = parse_options_parametrised(name, FOLDER_OPTIONS)
    template_or_resegment = options.pop('template_or_resegment', None)
    if template_or_resegment:
        if template_or_resegment == "resegment":
            options['resegment'] = True
        else:
            options["template"] = template_or_resegment
    return options


def parse_options_file(name):
    return parse_options_parametrised(name, FILE_OPTIONS)


def random_sizes(page_templates):
    return [t.photos_in_page() for t in page_templates if t.random]


def load_content(root_folder, page_templates):
    sizes = random_sizes(page_templates)
    list_content = []
    page_options = []
    for folder in sorted(f for f in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, f))):
        options = parse_options_folder(folder)
        im_list = []
        for file in sorted(os.listdir(os.path.join(root_folder, folder))):
            file_path = os.path.join(root_folder, folder, file)
            content = is_image(file_path)
            if content:
                im_list.append(content)
        len_imgs = len(im_list)
        len_template = len(get_photos_from_name(options.get('template'), page_templates))
        if len_template and len(im_list) > len_template:
            for i in range(0, len(im_list), len_template):
                sublist = im_list[i:i + len_template]
                if len(sublist) == len_template:
                    list_content.append(sublist)
                    page_options.append(options)
                else:  # do not force the wrong template!
                    segmented = segment(sublist, page_templates)
                    list_content += segmented
                    page_options += [{}] * len(segmented)
        elif len_imgs < len_template:  # ignore the template, it's wrong
            list_content += segment(im_list, page_templates)
        # we haven't forced a template and nothing is compatible, or forced resegment
        elif (not len_template and not any(sets_compatible(image_orientations(im_list), size) for size in sizes)) or options.get('resegment'):
            segmented = segment(im_list, page_templates)
            list_content += segmented
            page_options += [options] * len(segmented)
        else:
            list_content.append(im_list)
            page_options.append(options)

    return list_content, page_options


def get_photos_from_name(name, page_templates):
    template = next((t for t in page_templates if t.name == name), None)
    return template.photos_in_page() if template else []


def create_folder(name, destination):
    folder_path = os.path.join(destination, name)
    os.makedirs(folder_path)
    return folder_path


def segment(im_list, page_templates):
    """Transform a set into a list of subsets [s_1, ..., s_k] forming a partition
    we should for every s_i, |s_i| = r, \exists t \in page_templates s.t. holes(t) = r"""
    all_sizes = random_sizes(page_templates)
    partition = []
    while im_list:
        possible_sizes = all_sizes[:]
        compatible = False
        while possible_sizes and not compatible:
            i = random.choice(possible_sizes)
            possible_sizes.remove(i)
            compatible = sets_compatible(image_orientations(im_list[:len(i)]), i)
        if not compatible:
            possible_sizes = all_sizes[:]
            while possible_sizes and not compatible:
                i = random.choice(possible_sizes)
                possible_sizes.remove(i)
                orientations = image_orientations(im_list[:len(i)])
                compatible = sets_compatible(orientations, i, lax=True)
        new_set, im_list = im_list[:len(i)], im_list[len(i):]
        partition.append(new_set)
    return partition


def sets_compatible(im_set, template_set, lax=False):
    compatible = len(im_set) == len(template_set)
    if compatible and not lax:
        t_as = template_set.count('a')
        compatible = (
            im_set.count('h') <= template_set.count('h') + t_as
        and im_set.count('v') <= template_set.count('v') + t_as
        )
    return compatible


def in_to_out_folder(photo_folder):
    base_path, name = os.path.split(os.path.normpath(photo_folder))
    now = datetime.datetime.now().strftime("%H%M%S")
    new_name = 'pytex_' + now + "_" + name
    return os.path.join(base_path, new_name)


def cover_get_images(from_folder, images_partition, output_folder):
    try:
        get_image = lambda x: is_image(os.path.join(x[0], x[2][0]))
        cover_img = next((get_image(x) for x in os.walk(from_folder)))
    except Exception:
        raise Exception(f"Your folder {from_folder} should contain a cover image.")
    vignettes = image_mosaic(images_partition, output_folder, vertical=True)
    return [cover_img, vignettes]


def image_mosaic(images_partition, output_folder, vertical=True):
    all_images = [img for img_list in images_partition for img in img_list]
    all_squares = []
    subprocess.check_call(['mkdir', os.path.join(output_folder, 'mosaic')])
    for img in all_images:
        inputfile = shellify_filepath(img.filename)
        outputfile = os.path.join(output_folder, 'mosaic', 'sq' + re.sub('[^a-zA-Z0-9\.]', '', os.path.basename(img.filename)))
        command = 'convert ' + inputfile + r' -auto-orient -thumbnail 150x150^ -gravity center -extent 150x150 ' + outputfile
        subprocess.check_call(command, shell=True)
        all_squares.append(outputfile)
    outputfile = os.path.join(output_folder, 'mosaic', 'sq_montage.jpg')
    l = len(all_images)
    tiles = str(next((m for m in range(7, 17) if m % l == 0), 9))
    cmd = 'montage -mode Concatenate -geometry +5+5 -tile %s ' % tiles
    subprocess.check_call("%s %s %s" % (cmd, " ".join(all_squares), outputfile), shell=True)
    return is_image(outputfile)


def make_album(photo_folder, template_folder, filename):
    output_folder = in_to_out_folder(photo_folder)
    create_folder(output_folder, ".")

    t_main, files_opt = TemplateMain.load(template_folder)
    t_pages = TemplatePage.load(template_folder)

    imgs_part, options_p = load_content(photo_folder, t_pages)

    pages = [DocumentPage(im_set, t_pages, i + 1, output_folder, options)
             for i, im_set, options in zip(range(len(imgs_part)), imgs_part, options_p)]
    [p.write_to_disk() for p in pages]

    cover_page = []
    if TemplatePage.has_special(template_folder, PYTEX_COVER):
        cover_template = TemplatePage.load_special(template_folder, PYTEX_COVER)
        images = cover_get_images(photo_folder, imgs_part, output_folder)
        cover = DocumentPage(images, [cover_template], 0, output_folder)
        cover.write_to_disk()
        cover_page = [cover]

    main = DocumentMain(t_main, pages, output_folder, files_opt, cover_page)
    main.write_to_disk()

    os.chdir(output_folder)
    subprocess.check_call(['xelatex', OUTPUT_MAIN_NAME])
    if filename:
        subprocess.check_call(['mv', 'main.pdf', filename])
    return output_folder


def get_path(filename):
    """Return file's path or empty string if no path."""
    head, tail = os.path.split(filename)
    return head


def main_arguments_parser():
    default_template_folder = os.path.join(get_path(__file__), 'Latex')
    parser = argparse.ArgumentParser(description='Photo folder path', default_config_files=['.autophoto.rc','~/.autophoto.rc'])
    parser.add('-c', '--config', is_config_file=True, help='config file path')

    parser.add_argument('--name', '-n', default="",
                        type=str, nargs='?', help='Output filename')
    parser.add_argument('--album_name', '-a', default="Album",
                        type=str, nargs='?', help='Album title (used on the cover)')

    parser.add_argument('folder', default="./Photos",
                        type=str, help='Input photo folder')
    parser.add_argument('--template_folder', '-F', default=default_template_folder,
                        type=str, nargs='?', help='Input template folder')
    parser.add_argument('--template', '-t', default=DEFAULT_TEMPLATE,
                        type=str, nargs='?', help='Input template folder')
    return parser


def print_report(output_folder, warnings):
    print("\n\n\n")
    print(f"Output folder: {output_folder}")
    if warnings:
        print("\n\n\n***********************************************************")
        print()
        for warning in warnings:
            print(warning)
        print()
        print("***********************************************************")


def main():
    args = main_arguments_parser().parse_args()
    template_folder = os.path.join(args.template_folder, args.template)
    try:
        output_folder = make_album(args.folder, template_folder, args.name)
        print_report(output_folder, WARNINGS)
    except Exception as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
