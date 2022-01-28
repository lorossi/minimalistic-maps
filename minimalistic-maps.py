# https://taginfo.openstreetmap.org/ for reference
# https://gist.github.com/njanakiev/bb63108976815887545c0e9e6527b83c

from citymap import CityMap
from image import ImageCreator


def main():
    cities = ["Milano"]

    for city in cities:
        c = CityMap(city)

        i = ImageCreator()
        i.drawNodes(c.trees)
        outfile = f"output/{city}.png"
        i.save(outfile)


if __name__ == "__main__":
    main()
