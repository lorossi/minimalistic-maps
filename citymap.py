import logging

from time import sleep
from math import cos, sin, asin, radians, sqrt
from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder, Overpass


class CityMap:
    def __init__(self, city: str) -> None:
        """Create city map

        Args:
            city (str): City name
            radius (float, optional): City radius, in meters. Defaults to 3000.
        """
        self._city = city

        self._elements_dict = {}
        self._normalized_dict = {}
        self._features_list = []

        # request timing
        self._timeout = 60
        self._try_again = 10
        # initialize instances
        self._nominatim = Nominatim()
        self._overpass = Overpass()

    def __getattr__(self, feature: str) -> list[tuple[float, float]]:
        """Returns a list of features. Too check the available features, try using the features attribute

        Returns:
            list[tuple[float, float]]: list of relative positions
        """
        if feature in self._normalized_dict:
            return self._normalized_dict[feature]

        return []

    @property
    def features(self) -> list[str]:
        """Returns all loaded and normalized features

        Returns:
            list[str]
        """
        return [f for f in self._normalized_dict]

    @property
    def circular_features(self) -> dict[list[tuple[float, float]]]:
        """Returns all features that can must drawn as circles

        Returns:
            dict[list[tuple[float, float]]]
        """
        return {
            k: v
            for k, v in self._normalized_dict.items()
            if any(
                "node" in x["topology"] and x["name"] == k for x in self._features_list
            )
        }

    @property
    def polygonal_features(self) -> dict[list[tuple[float, float]]]:
        """Returns all features that can must drawn as polygons

        Returns:
            dict[list[tuple[float, float]]]
        """
        return {
            k: v
            for k, v in self._normalized_dict.items()
            if any(
                any(y in x["topology"] for y in {"way", "area"}) and x["name"] == k
                for x in self._features_list
            )
        }

    def loadCity(self) -> None:
        """Loads city area id and bounding box (both in xy and coordinates forms)"""
        city_query = self._nominatim.query(
            self._city,
            timeout=self._timeout,
        )
        # city area id
        self._area_id = city_query.areaId()
        # bounding box
        raw_bbox = city_query.toJSON()[0]["boundingbox"]
        self._bbox = (
            float(raw_bbox[0]),
            float(raw_bbox[2]),
            float(raw_bbox[1]),
            float(raw_bbox[3]),
        )

    def _coordsToXY(self, lat: float, lon: float) -> tuple[float, float]:
        """Calculates points x and y coordinates according to its latitude and longitude

        Args:
            lat (float)
            lon (float)

        Returns:
            tuple[float, float]: x, y coordinates
        """
        x = (lat - self._bbox[0]) / (self._bbox[2] - self._bbox[0])
        y = (lon - self._bbox[1]) / (self._bbox[3] - self._bbox[1])

        return x, y

    def _isPositionValid(self, *_) -> bool:
        """Is the provided position valid?

        Returns:
            bool:
        """
        raise NotImplementedError

    def _queryOSM(self, **kwargs) -> None:
        """Query OSM and load data into self._elements_dict

        Keyword args:
            name (str): Element type.
            tag (str): Element tag.
            topology (str): Element topology.
        """

        if not self._bbox:
            raise ValueError("Bounding Box not loaded.")

        self._elements_dict[kwargs["name"]] = []

        for t in kwargs["tag"]:
            query = overpassQueryBuilder(
                bbox=self._bbox,
                selector=t,
                elementType=kwargs["topology"],
                includeGeometry=True,
            )

            while True:
                try:
                    results = self._overpass.query(
                        query,
                        timeout=self._timeout,
                    )
                    break
                except Exception as _:
                    # OFC they couldn't raise proper exceptions.
                    # this exceptions is a "generic" exception.
                    logging.error(f"Trying again in {self._try_again} seconds...")
                    sleep(self._try_again)

            if not results.elements():
                continue

            if "node" in kwargs["topology"]:
                self._elements_dict[kwargs["name"]].extend(results.nodes())
            elif any(t in ["way", "area"] for t in kwargs["topology"]):
                self._elements_dict[kwargs["name"]].extend(results.ways())

    def _rotateCoordinates(self, coords: list[tuple[float, float]], angle: float = -90):
        """Rotates each coordinates around its center

        Args:
            coords (list[tuple[float, float]]): List of normalized coordinates
            angle (float, optional): Rotation angle. Defaults to -90.

        Returns:
            [type]: [description]
        """
        c = cos(radians(angle))
        s = sin(radians(angle))

        translated = [tuple(s - 0.5 for s in t) for t in coords]
        rotated = [(x * c - y * s, x * s + y * c) for x, y in translated]
        return [tuple(s + 0.5 for s in t) for t in rotated]

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
            coords = [
                self._coordsToXY(e.lat(), e.lon())
                for e in self._elements_dict[kwargs["name"]]
                if self._isPositionValid(e.lat(), e.lon())
            ]

            if not coords:
                return

            # rotate coordinates
            rotated = self._rotateCoordinates(coords)
            # add to dictionary
            self._normalized_dict[kwargs["name"]] = rotated

        elif any(t in ["way", "area"] for t in kwargs["topology"]):
            self._normalized_dict[kwargs["name"]] = []

            for element in self._elements_dict[kwargs["name"]]:
                for shape in element.geometry()["coordinates"]:
                    # sometimes shape are just an element
                    if len(shape) == 1:
                        shape = shape[0]

                    # filter coords and convert to xy
                    coords = [
                        self._coordsToXY(*s[::-1])
                        for s in shape
                        if self._isPositionValid(*s[::-1])
                    ]

                    # sometimes the coords list might be empty
                    if len(coords) < 3:
                        continue

                    # rotate coordinates
                    rotated = self._rotateCoordinates(coords)
                    # add to dictionary
                    self._normalized_dict[kwargs["name"]].append(rotated)

    def loadFeatures(self) -> None:
        """Loads and normalize all features."""
        for feature in self._features_list:
            self._queryOSM(**feature)
            self._normalizeElements(**feature)


class MinimalMap(CityMap):
    def __init__(self, city: str):
        super().__init__(city)
        self._features_list = [
            {"name": "benches", "tag": ["amenity=bench"], "topology": ["node"]},
            {
                "name": "traffic signals",
                "tag": ["traffic_signals"],
                "topology": ["node"],
            },
            {
                "name": "water fountains",
                "tag": ["amenity=drinking_water"],
                "topology": ["node"],
            },
        ]

    def _isPositionValid(self, *_) -> bool:
        "All positions are valid in the minimal map. There's no need to check if they are in bbox"
        return True


class RoundCityMap(CityMap):
    def __init__(self, city: str, radius: float = 3000):
        """Creates a round city

        Args:
            city (str): Name of the city
            radius (float, optional): City radius. Defaults to 3000.
        """
        super().__init__(city)

        self._radius = radius
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
            {
                "name": "parks",
                "tag": [
                    "leisure=park",
                    "leisure=garden",
                    "leisure=dog_park",
                    "leisure=pitch",
                    "landuse=green",
                    "landuse=grass",
                    "landuse=cemetery",
                ],
                "topology": ["area"],
            },
            {
                "name": "buildings",
                "tag": ["building"],
                "topology": ["way"],
            },
        ]

    def loadCity(self) -> None:
        """Loads city area id and bounding box (both in xy and coordinates forms)"""
        city_query = self._nominatim.query(
            self._city,
            timeout=self._timeout,
        )
        # city area id
        self._area_id = city_query.areaId()
        # city center cords
        self._city_center = tuple(
            float(city_query.toJSON()[0][x]) for x in ["lat", "lon"]
        )
        self._city_center_rad = tuple(radians(x) for x in self._city_center)

        self._calculateBBOX()

    def _calculateBBOX(self) -> None:
        """Calculates city area bounding box according to its center"""

        r_lat = radians(self._city_center[0])
        km_lat, km_lon = 110.574235, 110.572833 * cos(r_lat)
        d_lat = self._radius / 1000 / km_lat
        d_lon = self._radius / 1000 / km_lon

        self._bbox = (
            self._city_center[0] - d_lat,
            self._city_center[1] - d_lon,
            self._city_center[0] + d_lat,
            self._city_center[1] + d_lon,
        )

    def _distFromCityCenter(self, lat: float, lon: float) -> float:
        """Returns distance between a point and the city center coordinates

        Args:
            lat (float)
            lon (float)

        Returns:
            float: distance in meters
        """
        R = 6371
        r_lat, r_lon = radians(lat), radians(lon)
        d_lat, d_lon = (
            r_lat - self._city_center_rad[0],
            r_lon - self._city_center_rad[1],
        )

        a = (
            sin(d_lat / 2) ** 2
            + cos(r_lat) * cos(self._city_center_rad[0]) * sin(d_lon / 2) ** 2
        )
        c = 2 * asin(sqrt(a))

        return R * c * 1000  # meters

    def _isPositionValid(self, lat: float, lon: float) -> bool:
        """Checks whether the given point is indide the circle radius

        Args:
            lat (float): longitude of the point
            lon (float): latitude of the point

        Returns:
            bool
        """
        return self._distFromCityCenter(lat, lon) < self._radius
