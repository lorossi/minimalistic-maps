"""
Reference:

- Tags https://taginfo.openstreetmap.org/
- Snippets https://gist.github.com/njanakiev/bb63108976815887545c0e9e6527b83c
- OSMPythonTools https://github.com/mocnik-science/osm-python-tools
"""

from string import ascii_lowercase

from citymap import RoundCityMap, MinimalMap
from cityimage import CityImage, DarkCityImage


def main():
    cities = {
        "Milano, Italia": 3000,
        "Manhattan, NY": 10000,
        "Oslo, Norway": 3000,
        "Tokyo, Japan": 10000,
    }

    for city, radius in cities.items():
        filename = "".join(
            [
                c
                for c in city.lower().replace(" ", "-")
                if c in ascii_lowercase or c == "-"
            ]
        )

        r = RoundCityMap(city, radius)
        r.loadCity()
        r.loadFeatures()

        i = CityImage()

        i.drawTrees(r.trees)
        i.drawWater(r.water)
        i.drawParks(r.parks)
        i.drawBuildings(r.buildings)

        i.addTitle(city)
        i.save(f"output/{filename}-minimal.png")

        m = MinimalMap(city)
        m.loadCity()
        m.loadFeatures()

        colors = ["red", "green", "yellow", "blue"]

        for tag, coords in m.circular_features.items():
            title = f"{city} and its {len(coords)} {tag}"

            i = DarkCityImage()
            i.drawMultipleCircles(coords, fill=colors.pop(), radius=10)
            i.addTitle(title)
            i.save(f"output/{filename}-{tag}.png")


if __name__ == "__main__":
    main()
