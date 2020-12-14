import json
import time

from pathlib import Path
from PIL import Image, ImageFont, ImageDraw
from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder, Overpass


# constrains a value
def constrain(value, min, max):
    if value < min:
        value = min
    elif value > max:
        value = max
    return value

# translate variables
def map(value, old_min, old_max, new_min, new_max):
    old_width = old_max - old_min
    new_width = new_max - new_min
    value_scaled = float(value - old_min) / float(old_width)
    return new_min + (value_scaled * new_width)


class MinimalMap:
    def __init__(self, colors, width=1500, height=1500):
        self.width = width
        self.height = height
        self.colors = colors

        # start up apis
        self.nominatim = Nominatim()
        self.overpass = Overpass()

    def loadFont(self, main_font_path, italic_font_path):
        self.main_font_path = main_font_path
        self.italic_font_path = italic_font_path

    def setCity(self, city, timeout=300):
        self.city = city
        # select the city
        query = self.nominatim.query(self.city, timeout=timeout)
        self.area_id = query.areaId()

    def query(self, primary, secondary, timeout=300):
        # initialize list
        self.json_data = []
        # convert secondary to list
        if type(secondary) is not list:
            secondary = [secondary]

        # we save this variable to generate the output image name
        self.secondary_query = secondary

        # load each selector
        for s in secondary:
            # effective query
            selector = f'"{primary}"="{s}"'
            query = overpassQueryBuilder(area=self.area_id, elementType='node',
                                         selector=selector, out='body')
            while True:
                try:
                    result = self.overpass.query(query, timeout=timeout)
                    break
                except Exception as e:
                    print(f"Error while querying {self.city}, {selector}. Error {e}")
                    print("Trying again in a bit")
                    time.sleep(30)

            # convert to json and keep only the nodes
            result_json = result.toJSON()["elements"]
            self.json_data.extend(result_json)  # keep only the elements

        lat = sorted([x["lat"] for x in self.json_data])
        lon = sorted([x["lon"] for x in self.json_data])

        self.bbox = {
            "north": lat[0],
            "south": lat[-1],
            "east": lon[-1],
            "west": lon[0],
            "height": lat[-1] - lat[0],
            "width": lon[-1] - lon[0]
        }

    def createImage(self, subtitle="", map_scl=.75):
        if len(self.json_data) > 10000:
            circles_radius = 1
        elif len(self.json_data) > 1000:
            circles_radius = 2
        else:
            circles_radius = 3
        # calculate map image size
        biggest = max(self.bbox["width"], self.bbox["height"])
        scl = max(self.width, self.height) / biggest

        # map width and height
        map_width = int(self.bbox["width"] * scl)
        map_height = int(self.bbox["height"] * scl)

        # create the map image
        map_im = Image.new('RGBA', (map_width, map_height),
                           color=self.colors["secondary"])
        map_draw = ImageDraw.Draw(map_im)

        # draw points
        for node in self.json_data:
            # calculate each node position
            x = map(node["lon"], self.bbox["east"],
                    self.bbox["west"], 0, map_im.width)
            y = map(node["lat"], self.bbox["south"], self.bbox["north"],
                    0, map_im.height)
            circle_box = [x - circles_radius, y - circles_radius,
                          x + circles_radius, y + circles_radius]
            # finally draw circle
            map_draw.ellipse(circle_box, fill=self.colors["fill"])

        # scale the image
        new_width = int(map_width * map_scl)
        new_height = int(map_height * map_scl)
        map_im = map_im.resize((new_width, new_height))
        # calculate map image displacement
        dx = int((self.width - map_im.width) / 2)
        dy = int((self.height - map_im.height) / 2)

        # create the text image
        text_im = Image.new('RGBA', (self.width, self.height),
                            color=self.colors["secondary"])
        text_draw = ImageDraw.Draw(text_im)

        # city name format
        text = self.city
        font_size = constrain((dy * 2 / 3), 40, 100)
        # main text location
        tx = font_size / 2
        ty = self.height - font_size / 2
        main_font = ImageFont.truetype(font=self.main_font_path,
                                       size=font_size)

        text_draw.text((tx, ty), text=text, anchor="ls",
                       fill=self.colors["text"], font=main_font,
                       align="left", stroke_fill=None)

        # watermark
        # city name format
        text = "Lorenzo Rossi - www.lorenzoros.si"
        font_size = constrain((dy * 1 / 3), 15, 35)
        italic_font = ImageFont.truetype(font=self.italic_font_path,
                                         size=font_size)
        # create a new image with just the right size
        watermark_im = Image.new('RGBA', (self.width, font_size),
                                 color=self.colors["secondary"])

        watermark_draw = ImageDraw.Draw(watermark_im)
        watermark_draw.text((watermark_im.width, watermark_im.height),
                            text=text, font=italic_font, anchor="rd",
                            fill=self.colors["watermark"], stroke_fill=None)
        # rotate text
        watermark_im = watermark_im.rotate(angle=90, expand=1)

        # watermark location
        tx = int(self.width - font_size * 1.5)
        ty = int(font_size * 1.5)
        # paste watermark into text
        text_im.paste(watermark_im, (tx, ty))

        # final image
        self.dest_im = Image.new('RGBA', (self.width, self.height),
                                 color=self.colors["secondary"])

        # paste into final image
        self.dest_im.paste(text_im)
        self.dest_im.paste(map_im, (dx, dy))

    def saveImage(self, path):
        filename = f"{self.city}-{'-'.join(self.secondary_query)}.png"
        full_path = f"{path}/{filename}"
        self.dest_im.save(full_path)


def main():
    # color palette
    # https://coolors.co/ffa400-009ffd-2a2a72-232528-eaf6ff

    with open("settings.json") as f:
        settings = json.load(f)

    # settings unpacking
    image_width = settings["image"]["width"]
    image_height = settings["image"]["height"]
    output_folder = settings["image"]["output_path"]
    cities = sorted(settings["cities"])
    main_font = settings["image"]["main_font"]
    italic_font = settings["image"]["italic_font"]
    colors = settings["image"]["colors"]

    # create output folder
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    # create city
    m = MinimalMap(colors, width=image_width, height=image_height)
    # load fonts
    m.loadFont(main_font, italic_font)

    # load queries

    for city in cities:
        output_path = f"{output_folder}/{city}/"
        # make output city folder
        Path(output_path).mkdir(parents=True, exist_ok=True)
        m.setCity(city)
        for query in settings["queries"]:
            m.query(query["primary_query"], query["secondary_query"])
            m.createImage(subtitle=query["subtitle"])
            m.saveImage(output_path)

    print("Done")

if __name__ == "__main__":
    main()
