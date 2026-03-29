from PIL import Image
from colorthief import ColorThief
import webcolors
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("CLARIFAI_PAT")





#uses webcolors to find closest color
def closest_color(requested_color):
    min_colors = {}
    for name in webcolors.names("css3"):
        r_c, g_c, b_c = webcolors.hex_to_rgb(webcolors.name_to_hex(name))
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colors[(rd + gd + bd)] = name
    return min_colors[min(min_colors.keys())]




#uses webcolors to get color name
def get_color_name(rgb_tuple):
    try:
        # Convert RGB to hex
        hex_value = webcolors.rgb_to_hex(rgb_tuple)
        # Get the color name directly
        return webcolors.hex_to_name(hex_value)
    except ValueError:
        # If exact match not found, find the closest color
        return closest_color(rgb_tuple)




# color theory checker
def get_delta_e(color1_rgb, color2_rgb):
    r1, g1, b1 = color1_rgb
    r2, g2, b2 = color2_rgb
    return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5


def do_they_match(top_palette, bottom_palette, top_name, bottom_name):

    # Colors that are neutrals - go with almost everything
    neutrals = ["white", "black", "grey", "gray", "beige", "cream", "ivory",
                "navy", "tan", "brown", "khaki", "charcoal"]

    # Check if either is a neutral
    top_is_neutral = any(n in top_name for n in neutrals)
    bottom_is_neutral = any(n in bottom_name for n in neutrals)

    if top_is_neutral or bottom_is_neutral:
        return "This outfit works together!"

    # Same color family = monochromatic = generally fine
    color_families = [
        ["blue", "navy", "slate", "steel", "sky", "cobalt", "teal", "cyan"],
        ["red", "crimson", "scarlet", "maroon", "rose"],
        ["green", "olive", "lime", "forest", "sage"],
        ["purple", "violet", "lavender", "plum", "indigo"],
        ["orange", "amber", "coral", "peach"],
        ["pink", "blush", "magenta", "fuchsia"],
        ["yellow", "gold", "mustard"],
        ["brown", "tan", "camel", "rust", "copper"],
    ]

    top_family = None
    bottom_family = None

    for family in color_families:
        if any(c in top_name for c in family):
            top_family = family
        if any(c in bottom_name for c in family):
            bottom_family = family

    # Same family = monochromatic outfit, totally fine
    if top_family and bottom_family and top_family == bottom_family:
        return "This outfit works together! (monochromatic look)"

    # True clashes - these are the only real problem pairs
    true_clashes = [
        ("red", "orange"),
        ("red", "pink"),
        ("orange", "pink"),
        ("yellow", "purple"),
        ("green", "red"),
    ]

    for pair in true_clashes:
        if (any(pair[0] in c for c in [top_name]) and any(pair[1] in c for c in [bottom_name])) or \
           (any(pair[1] in c for c in [top_name]) and any(pair[0] in c for c in [bottom_name])):
            return f"This outfit may clash! {top_name} and {bottom_name} don't work well together."

    # Everything else is fine
    return "This outfit works together!"


def main():
    count = 0
    colors = {}
    x = input("Please input the filepath for your clothing(-1 if finished): ") #taking image input
    while x != "-1":

        with Image.open(x) as image: #opening image
            width, height = image.size

            top_half = (0, 0, width, height // 2)       #determining top half of image
            bottom_half =(0, height // 2, width, height)    #determining bottom half of image

            cropped_top = image.crop(top_half)              #cropping top
            cropped_bottom = image.crop(bottom_half)           #cropping bottom

            cropped_top.save("temp_top.png")        #saving top crop
            cropped_bottom.save("temp_bottom.png")  #saving bottom crop

            top_palette = ColorThief(".venv/temp_top.png").get_palette(color_count=3, quality=1)
            bottom_palette = ColorThief(".venv/temp_bottom.png").get_palette(color_count=3, quality=1)

            colors[f"top{count}"] = top_palette
            colors[f"bottom{count}"] = bottom_palette
            top_name = get_color_name(top_palette[0])
            bottom_name = get_color_name(bottom_palette[0])
            print(f"Top color: {top_name}")
            print(f"Bottom color: {bottom_name}")
            result = do_they_match(top_palette, bottom_palette, top_name, bottom_name)
            print(result)
            count += 1

            x = input("Please input the filepath for your clothing(-1 if finished): ")
    print(colors)
    return colors


