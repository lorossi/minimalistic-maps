import json
import osm2geojson

from PIL import Image, ImageFont, ImageDraw
from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder, Overpass


# translate variables
def map(value, old_min, old_max, new_min, new_max):
    old_width = old_max - old_min
    new_width = new_max - new_min
    value_scaled = float(value - old_min) / float(old_width)
    return new_min + (value_scaled * new_width)


class Citymap:
    def __init__(self, colors, city="Milano", width=1500, height=1500):
        self.city = city
        self.width = width
        self.height = height
        self.colors = colors
        # colors = {
        #   background: "...",
        #   text: "..."
        # }

        # identify the city
        self.nominatim = Nominatim()
        self.overpass = Overpass()

    def loadFont(self, main_font_path, italic_font_path):
        self.main_font_path = main_font_path
        self.italic_font_path = italic_font_path

    def query(self, primary, secondary):
        # initialize list
        self.json_data = []
        # convert secondary to list
        if type(secondary) is not list:
            secondary = [secondary]

        # we save this variable to generate the output image
        self.secondary_query = secondary
        # select the city
        query = self.nominatim.query(self.city)

        box_list = [float(x) for x in query.toJSON()[0]["boundingbox"]]
        self.bbox = {
            "north": box_list[1],
            "south": box_list[0],
            "east": box_list[2],
            "west": box_list[3],
            "height": box_list[1] - box_list[0],
            "width": box_list[3] - box_list[2]
        }

        self.area_id = query.areaId()

        # load each selector
        for s in secondary:
            # effective query
            selector = f'"{primary}"="{s}"'
            query = overpassQueryBuilder(area=self.area_id, elementType='node',
                                         selector=selector, out='body')

            result = self.overpass.query(query, timeout=60)
            # convert to json and keep only the nodes
            result_json = result.toJSON()["elements"]
            self.json_data.extend(result_json)  # keep only the elements

        # load city boundary
        selector = ['"boundary"="administrative"', '"admin_level"="8"']
        query = overpassQueryBuilder(area=self.area_id, elementType='relation',
                                     selector=selector, out='body',
                                     includeGeometry=True)

        result = self.overpass.query(query)
        geojson = osm2geojson.json2shapes(result.toJSON())

        self.polygon_coords = []
        for point in geojson[0]["shape"]:
            self.polygon_coords.extend(point.exterior.coords[:-1])

    def createImage(self, subtitle="", map_scl=.95):
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

        # now start drawing

        # extract boundary lines
        polygon_points = []
        for point in self.polygon_coords:
            x = map(point[0], self.bbox["east"],
                    self.bbox["west"], 0, map_im.width)
            y = map(point[1], self.bbox["south"], self.bbox["north"],
                    0, map_im.height)
            polygon_points.append((x, y))
        # draw boundary
        map_draw.polygon(polygon_points, outline=self.colors["boundary"])

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

        # main text format
        text = self.city
        font_size = int(dy * 2 / 3)
        # main text location
        tx = self.width / 2
        ty = font_size / 2

        main_font = ImageFont.truetype(font=self.main_font_path,
                                       size=font_size)
        text_draw.text((tx, ty), text=text, anchor="mt",
                       fill=self.colors["primary"], font=main_font,
                       align='center', stroke_fill=None)

        # main text format
        text = subtitle.replace("%n", str(len(self.json_data)))
        font_size = int(dy * 1 / 3)
        # italic text locatin
        tx = self.width / 2
        ty = self.height - font_size / 2

        italic_font = ImageFont.truetype(font=self.italic_font_path,
                                         size=font_size)
        text_draw.text((tx, ty), text=text, anchor="mb",
                       fill=self.colors["primary"], font=italic_font,
                       align='center', stroke_fill=None)

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
    # https://coolors.co/011627-ff3366-2ec4b6-f6f7f8-20a4f3
    # https://coolors.co/721817-fa9f42-2b4162-0b6e4f-e0e0e2

    with open("settings.json") as f:
        settings = json.load(f)
    output_path = "output/"

    # settings unpacking
    image_width = settings["image"]["width"]
    image_height = settings["image"]["height"]
    city = settings["image"]["city"]
    main_font = settings["image"]["main_font"]
    italic_font = settings["image"]["italic_font"]
    colors = settings["image"]["colors"]

    # create city
    city = Citymap(colors, width=image_width, height=image_height, city=city)
    # load fonts
    city.loadFont(main_font, italic_font)

    # load queries

    for query in settings["queries"]:
        city.query(query["primary_query"], query["secondary_query"])
        city.createImage(subtitle=query["subtitle"])
        city.saveImage(output_path)


if __name__ == "__main__":
    main()
