from PIL import Image
from colorthief import ColorThief
import webcolors





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
    clashes = []

    for top_color in top_palette:
        for bottom_color in bottom_palette:
            delta_e = get_delta_e(top_color, bottom_color)

            if delta_e < 30:
                clashes.append("too similar")
            elif delta_e < 100:
                bad_pairs = [
                    ("red", "green"),
                    ("navy", "black"),
                    ("blue", "purple"),
                    ("orange", "purple"),
                    ("red", "orange"),
                    ("darkgreen", "brown"),
                    ("blue", "grey")
                ]
                for pair in bad_pairs:
                    if (pair[0] in top_name and pair[1] in bottom_name) or \
                            (pair[1] in top_name and pair[0] in bottom_name):
                        clashes.append(f"{top_name} and {bottom_name}")

    if clashes:
        return "This outfit may clash! If unsure try another combination."
    else:
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
            do_they_match(top_palette, bottom_palette, top_name, bottom_name)
            count += 1

            x = input("Please input the filepath for your clothing(-1 if finished): ")
    print(colors)
    return colors
main()

