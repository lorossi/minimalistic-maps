"""
Reference:

- Tags https://taginfo.openstreetmap.org/
- Snippets https://gist.github.com/njanakiev/bb63108976815887545c0e9e6527b83c
- OSMPythonTools https://github.com/mocnik-science/osm-python-tools
- Colors https://www.w3schools.com/colors/colors_crayola.asp
"""

import logging
from string import ascii_lowercase

from citymap import RoundCityMap, MinimalMap
from cityimage import CityImage, DarkCityImage, MinimalisticCityImage


def main():
    # logging config
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s: %(message)s",
    )

    logging.info("Script started")

    # list of cities and their radii
    cities = {
        "Milano, Italia": 3000,
        "Paris, France": 3000,
        "Berlin, Germany": 3000,
        "Barcellona, Spain": 3000,
        "Amsterdam, the Netherlands": 3000,
        "Prague, Czechia": 3000,
        "Budapest, Hungary": 3000,
    }

    for city, radius in cities.items():
        # format filename
        filename = "".join(
            [
                c
                for c in city.lower().replace(" ", "-")
                if c in ascii_lowercase or c == "-"
            ]
        )

        # load the city and its features
        logging.info(f"Creating round map for {city}")
        r = RoundCityMap(city, radius)
        logging.info("Loading city")
        r.loadCity()
        logging.info("Loading features")
        r.loadFeatures()

        # create the first circular image
        logging.info("Creating image")
        m = CityImage()
        m.drawTrees(r.trees)
        m.drawWater(r.water)
        m.drawParks(r.parks)
        m.drawBuildings(r.buildings)

        m.drawTitle(city)
        logging.info(f"Saving image {filename}")
        m.save(f"output/{filename}-minimal.png")

        # create the second circular image (black and white)
        d = DarkCityImage()
        d.drawTrees(r.trees)
        d.drawWater(r.water)
        d.drawParks(r.parks)
        d.drawBuildings(r.buildings)

        d.drawTitle(city)
        logging.info(f"Saving image {filename} dark")
        d.save(f"output/{filename}-minimal-dark.png")

        logging.info(f"Creating minimal map for {city}")
        # create the minimal map for the city
        m = MinimalMap(city)
        logging.info("Loading city")
        m.loadCity()
        logging.info("Loading features")
        m.loadFeatures()

        for tag, coords in m.circular_features.items():
            # create a minimal map for each feature in the city
            city_name = city.split(",")[0]
            title = f"{city_name} and its {len(coords)} {tag}"
            fill = m.getColor(tag)
            logging.info(f"Creating image with {tag}: found {len(coords)}")
            i = MinimalisticCityImage()
            i.drawMultipleCircles(coords, fill=fill, radius=10)
            i.drawTitle(title)
            logging.info(f"Saving image {filename}-{tag.replace(' ',  '-')}")
            i.save(f"output/{filename}-{tag.replace(' ',  '-')}.png")


if __name__ == "__main__":
    main()
