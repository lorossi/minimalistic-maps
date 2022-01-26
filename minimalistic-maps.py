# https://taginfo.openstreetmap.org/ for reference
# https://gist.github.com/njanakiev/bb63108976815887545c0e9e6527b83c

from citymap import CityMap
from image import ImageCreator


def main():
    cities = ["Milano", "Rome", "Florence"]

    for city in cities:
        c = CityMap(city)
        c.loadTrees()

        i = ImageCreator()
        i.drawTrees(c.trees)
        i.save(city.lower())


if __name__ == "__main__":
    main()
