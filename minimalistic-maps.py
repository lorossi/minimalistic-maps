"""
Reference:

- Tags https://taginfo.openstreetmap.org/
- Snippets https://gist.github.com/njanakiev/bb63108976815887545c0e9e6527b83c
- OSMPythonTools https://github.com/mocnik-science/osm-python-tools
"""


from citymap import RoundCityMap
from cityimage import CityImage
from string import ascii_lowercase


def main():
    cities = ["Milano, Italia"]

    for city in cities:
        c = RoundCityMap(city)
        c.loadCity()
        c.loadFeatures()

        i = CityImage(background_color=(240, 240, 240))

        i.drawTrees(c.trees)
        i.drawWater(c.water)
        i.drawParks(c.parks)
        i.drawBuildings(c.buildings)

        filename = "".join(
            [c for c in city.lower() if c in ascii_lowercase or c == " "]
        ).replace(" ", "-")
        outfile = f"output/{filename}-minimal.png"
        i.addTitle(city)
        i.save(outfile)

        i = CityImage(background_color=(15, 15, 15))


if __name__ == "__main__":
    main()
