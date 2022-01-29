from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder, Overpass
from math import cos, sin, radians

import itertools
import copy


class CityMap:
    def __init__(self, city: str) -> None:
        self._city = city
        self._elements_dict = {}
        self._normalized_dict = {}
        self._features_list = [
            {
                "name": "trees",
                "tag": ["natural=tree"],
                "topology": ["node"],
            },
            {
                "name": "water",
                "tag": ["natural=water"],
                "topology": ["way"],
            },
        ]

        self._timeout = 60

        self._nominatim = Nominatim()
        self._overpass = Overpass()
        self._loadCity()

    def _loadCity(self) -> None:
        """Loads city area id and bounding box (both in xy and coordinates forms)"""
        city_query = self._nominatim.query(
            self._city,
            timeout=self._timeout,
        )
        # city area id
        self._area_id = city_query.areaId()
        # city coords bounding box (lat-lat, lon-lon)
        self._bbox = tuple(float(x) for x in city_query.toJSON()[0]["boundingbox"])
        # city bounding coordinates in xy format
        self._xy_bbox = tuple(
            itertools.chain.from_iterable(
                self._coordsToXY(self._bbox[x], self._bbox[x + 2]) for x in [0, 1]
            )
        )
        # map scale
        self._scl = max(abs(self._xy_bbox[x] - self._xy_bbox[x + 2]) for x in [0, 1])

    def _queryOSM(self, **kwargs) -> None:
        """Query OSM and load data into self._elements_dict

        Keyword args:
            name (str): Element type.
            tag (str): Element tag.
            topology (str): Element topology.
        """
        self._elements_dict[kwargs["name"]] = []

        for t in kwargs["tag"]:
            query = overpassQueryBuilder(
                area=self._area_id,
                selector=t,
                elementType=kwargs["topology"],
                includeGeometry=True,
            )

            results = self._overpass.query(
                query,
                timeout=self._timeout,
            )

            if not results.elements():
                continue

            if "node" in kwargs["topology"]:
                self._elements_dict[kwargs["name"]].extend(results.nodes())
            elif "way" in kwargs["topology"]:
                self._elements_dict[kwargs["name"]].extend(results.ways())

    def _normalizeElements(self, **kwargs) -> None:
        """Creates an entry in self._normalized_dict for a set of positions in self._elements_dict.
        The resulting coordinates are a list of (x, y) tuples in range [0, 1]x[0, 1], relative to
        the bounding box of the coordinates themselves.

        Keyword args:
            name (str): Element type.
            tag (str): Element tag.
            topology (str): Element topology.
        """

        if "node" in kwargs["topology"]:
            # extract coordinates
            pos = [
                self._coordsToXY(e.lat(), e.lon())
                for e in self._elements_dict[kwargs["name"]]
            ]

            # normalize and return coordinates
            self._normalized_dict[kwargs["name"]] = [
                tuple(abs(p[x] - self._xy_bbox[x]) / self._scl for x in [0, 1])
                for p in pos
            ]

            # print(self._normalized_dict[kwargs["name"]])

        elif "way" in kwargs["topology"]:
            self._normalized_dict[kwargs["name"]] = []

            for element in self._elements_dict[kwargs["name"]]:
                for shape in element.geometry()["coordinates"]:
                    if len(shape) == 1:
                        shape = shape[0]

                    # LONGITUDE AND LATITUDE ARE REVERSED! WTF
                    pos = [self._coordsToXY(*s[::-1]) for s in shape]

                    self._normalized_dict[kwargs["name"]].append(
                        [
                            tuple(
                                abs(p[x] - self._xy_bbox[x]) / self._scl for x in [0, 1]
                            )
                            for p in pos
                        ]
                    )

    def _coordsToXY(self, lat: float, lon: float) -> tuple[float, float]:
        """Converts lat, loon coordinates to x, y coordinates

        Args:
            lat (float): latitude
            lon (float): longitude

        Returns:
            tuple[float, float]
        """

        R = 6371
        r_lat, r_lon = radians(lat), radians(lon)
        x = R * cos(r_lat) * cos(r_lon)
        y = R * cos(r_lat) * sin(r_lon)

        return x, y

    def loadFeatures(self) -> None:
        for feature in self._features_list:
            self._queryOSM(**feature)
            self._normalizeElements(**feature)

    @property
    def trees(self) -> list[tuple[float, float]]:
        """List of normalized coords for trees

        Returns:
            list[tuple[float, float]]: list of normalized coords
        """
        return copy.deepcopy(self._normalized_dict["trees"])

    @property
    def water(self) -> list[list[tuple[float, float]]]:
        """List of normalized coords for water bodies

        Returns:
            list[tuple[float, float]]: list of normalized coords
        """
        return copy.deepcopy(self._normalized_dict["water"])
