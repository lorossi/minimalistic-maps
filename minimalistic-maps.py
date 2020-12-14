import json
import time
import logging

from shutil import rmtree
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

    def query(self, primary, secondary, element_type, timeout=300):
        # save the element type
        self.element_type = element_type
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
            query = overpassQueryBuilder(area=self.area_id,
                                         elementType=self.element_type,
                                         selector=selector, out='body',
                                         includeGeometry=True)
            while True:
                try:
                    result = self.overpass.query(query, timeout=timeout)
                    break
                except KeyboardInterrupt:
                    logging.info("Received KeyboardInterrupt while querying. "
                                 "Stopping execution.")
                    quit()
                except Exception as e:
                    logging.warning(f"Error while querying {self.city}, "
                                    f" {selector}. Error {e}. \n"
                                    "Trying again in a bit")
                    time.sleep(30)

            if self.element_type == "node":
                # convert to json and keep only the nodes
                result_json = result.toJSON()["elements"]
                self.json_data.extend(result_json)  # keep only the elements

            elif self.element_type == "way":
                # this is going to be fun, it's a polygon!
                result_json = result.toJSON()["elements"]
                for r in result_json:
                    self.json_data.append(r["geometry"])

        if self.element_type == "node":
            lat = sorted([x["lat"] for x in self.json_data])
            lon = sorted([x["lon"] for x in self.json_data])

        elif self.element_type == "way":
            lat = []
            lon = []
            # i'm sure there's a list comprehension for this
            for way in self.json_data:
                for point in way:
                    lat.append(point["lat"])
                    lon.append(point["lon"])

            lat = sorted(lat)
            lon = sorted(lon)

        self.bbox = {
            "north": lat[0],
            "south": lat[-1],
            "east": lon[-1],
            "west": lon[0],
            "height": lat[-1] - lat[0],
            "width": lon[-1] - lon[0]
        }


    def createImage(self, fill="red", subtitle="", map_scl=.9):
        if len(self.json_data) > 10000:
            circles_radius = 0.5
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
        if self.element_type == "node":
            for node in self.json_data:
                # calculate each node position
                x = map(node["lon"], self.bbox["east"],
                        self.bbox["west"], 0, map_im.width)
                y = map(node["lat"], self.bbox["south"], self.bbox["north"],
                        0, map_im.height)
                circle_box = [x - circles_radius, y - circles_radius,
                              x + circles_radius, y + circles_radius]
                # finally draw circle
                map_draw.ellipse(circle_box, fill=fill)

        # draw shapes
        elif self.element_type == "way":
            # iterate throught shapes
            for way in self.json_data:
                poly = []
                # iterate throught points
                for point in way:
                    # calculate each point position
                    x = map(point["lon"], self.bbox["east"],
                            self.bbox["west"], 0, map_im.width)
                    y = map(point["lat"], self.bbox["south"], self.bbox["north"],
                            0, map_im.height)
                    poly.append((x, y))
                # finally draw poly
                map_draw.polygon(poly, fill=fill)

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
        font_size = int(constrain((dy * 2 / 3), 40, 100))

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
        font_size = int(constrain((dy * 1 / 3), 15, 35))
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
    logfile = __file__.replace(".py", ".log")
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s",
                        level=logging.INFO, filename=logfile,
                        filemode="w+")
    print(f"Logging into {logfile}")
    logging.info("Script started")

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
    logging.info("Settings loaded")

    # delete output folder
    rmtree(output_folder)
    # create output folder
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    # create city
    m = MinimalMap(colors, width=image_width, height=image_height)
    # load fonts
    m.loadFont(main_font, italic_font)
    logging.info("Basic setup completed")

    # load queries
    for city in cities:
        output_path = f"{output_folder}/{city}/"
        # make output city folder
        Path(output_path).mkdir(parents=True, exist_ok=True)
        m.setCity(city)
        for query in sorted(settings["queries"], key=lambda x: x["subtitle"]):
            m.query(query["primary_query"], query["secondary_query"],
                    query["type"])
            m.createImage(fill=query["fill"], subtitle=query["subtitle"])
            m.saveImage(output_path)
            logging.info(f"Generated {' '.join(query['secondary_query'])}"
                         f" for city {city}")

        logging.info(f"{city} completed")

    print("Done")
    logging.info("Everything done!")


if __name__ == "__main__":
    main()
