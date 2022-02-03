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
from cityimage import CityImage, DarkCityImage


def main():
    logging.info("Script started")

    cities = {
        "Milano, Italia": 3000,
        "Paris, France": 5000,
        "Berlin, Germany": 3000,
        "Barcellona, Spain": 3000,
    }

    for city, radius in cities.items():
        filename = "".join(
            [
                c
                for c in city.lower().replace(" ", "-")
                if c in ascii_lowercase or c == "-"
            ]
        )

        logging.info(f"Creating round map for {city}")
        r = RoundCityMap(city, radius)
        logging.info("Loading city")
        r.loadCity()
        logging.info("Loading features")
        r.loadFeatures()

        logging.info("Creating image")
        i = CityImage()
        i.drawTrees(r.trees)
        i.drawWater(r.water)
        i.drawParks(r.parks)
        i.drawBuildings(r.buildings)

        i.addTitle(city)
        logging.info(f"Saving image {filename}")
        i.save(f"output/{filename}-minimal.png")

        logging.info(f"Creating minimal map for {city}")
        m = MinimalMap(city)
        logging.info("Loading city")
        m.loadCity()
        logging.info("Loading features")
        m.loadFeatures()

        for tag, coords in m.circular_features.items():
            title = f"{city} and its {len(coords)} {tag}"
            fill = m.getColor(tag)
            logging.info(f"Creating image with {tag}: found {len(coords)}")
            i = DarkCityImage()
            i.drawMultipleCircles(coords, fill=fill, radius=10)
            i.addTitle(title)
            logging.info(f"Saving image {filename}-{tag}")
            i.save(f"output/{filename}-{tag}.png")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s: %(message)s",
    )
    main()
