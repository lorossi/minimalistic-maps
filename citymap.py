from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder, Overpass
from math import cos, sin, radians


class CityMap:
    def __init__(self, city: str) -> None:
        self._city = city
        self._elements_dict = {}
        self._normalized_dict = {}
        self._tags_dict = {"trees": "natural=tree"}

        self._timeout = 60

        self._nominatim = Nominatim()
        self._overpass = Overpass()

        self._area_id = self._nominatim.query(
            self._city,
            timeout=self._timeout,
        ).areaId()

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

        return (x, y)

    def _getBoundingBox(
        self, pos: list[float, float]
    ) -> tuple[float, float, float, float]:
        """Returns bounding box for a set of points

        Args:
            pos (list[float, float]): List of points

        Returns:
            tuple[float, float, float, float]: top left and bottom right coordinates
        """
        return (
            min(p[0] for p in pos),
            max(p[1] for p in pos),
            max(p[0] for p in pos),
            min(p[1] for p in pos),
        )

    def _normalizeElements(self, key: str) -> None:
        """Creates an entry in self._normalized_dict for a set of positions in self._elements_dict.
        The resulting coordinates are a list of (x, y) tuples in range [0, 1]x[0, 1], relative to
        the bounding box of the coordinates themselves.

        Args:
            key (str): key belonging to the self._tags_dict dictionary
        """
        # extract coordinates
        pos = [self._coordsToXY(e.lat(), e.lon()) for e in self._elements_dict[key]]
        # get bounding box
        bbox = self._getBoundingBox(pos)
        # calculate scale
        scl = max(abs(bbox[x] - bbox[x + 2]) for x in range(2))
        # normalize and return coordinates
        self._normalized_dict[key] = [
            (abs(p[0] - bbox[0]) / scl, abs(p[1] - bbox[1]) / scl) for p in pos
        ]

    def _loadNodes(self, element_tag: str) -> None:
        """Loads into self._elements_dict a set of nodes.

        Args:
            element_tag (str): Nodes tag, as found in self._elements_dict
        """
        query = overpassQueryBuilder(
            area=self._area_id,
            selector=element_tag,
            elementType="node",
        )

        self._elements_dict[element_tag] = self._overpass.query(
            query,
            timeout=self._timeout,
        ).nodes()

    @property
    def trees(self) -> list[tuple[float, float]]:
        """List of normalized coords for trees

        Returns:
            list[tuple[float, float]]: list of normalized coords
        """
        trees_tag = self._tags_dict["trees"]
        self._loadNodes(trees_tag)
        self._normalizeElements(trees_tag)
        return [x for x in self._normalized_dict[trees_tag]]
