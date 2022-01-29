"""
Reference:

- Tags https://taginfo.openstreetmap.org/
- Snippets https://gist.github.com/njanakiev/bb63108976815887545c0e9e6527b83c
- OSMPythonTools https://github.com/mocnik-science/osm-python-tools
"""


from citymap import CityMap
from image import ImageCreator


def main():
    cities = ["Milano"]

    for city in cities:
        c = CityMap(city)
        c.loadFeatures()

        i = ImageCreator()
        i.drawTrees(c.trees)
        i.drawWater(c.water)

        outfile = f"output/{city}.png"
        i.save(outfile)


if __name__ == "__main__":
    main()
