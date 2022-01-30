from PIL import Image, ImageDraw


class ImageCreator:
    def __init__(self, width: int = 2000, height: int = 2000, scl: float = 0.8):
        self._sizes = (width, height)
        self._scl = scl
        self._border = tuple(s * (1 - self._scl) / 2 for s in self._sizes)

        self._image = Image.new("RGB", self._sizes, "white")
        self._draw = ImageDraw.Draw(self._image)

    def _drawCircle(
        self,
        coords: tuple[int, int],
        r: float = 1,
        fill: tuple[int, int, int, int] | str = "black",
    ) -> None:
        """Draws a circle according to its relative position (in range [0-1] for both x and y)

        Args:
            coords (tuple[int, int]): circle center coordinates
            r (float, optional): Circle radius. Defaults to 1.
            fill (tuple[int, int, int, int] | str, optional): Fill color. Defaults to "black".
        """
        # arc bounding box
        xy = (coords[0] - r, coords[1] - r, coords[0] + r, coords[1] + r)

        self._draw.ellipse(xy, fill=fill)

    def _drawMultipleCircles(
        self,
        coords: list[tuple[int, int]],
        r: float = 1,
        fill: tuple[int, int, int, int] | str = "black",
    ) -> None:
        """Draws multiple circles from a list of relative positions (in range [0-1] for both x and y)

        Args:
            coords (tuple[int, int]): circle center coordinates
            r (float, optional): Circle radius. Defaults to 1.
            fill (tuple[int, int, int, int] | str, optional): Fill color. Defaults to "black".
        """

        for c in coords:
            abs_coords = self._relativeToAbsolute(c)
            self._drawCircle(abs_coords, r, fill)

    def _drawPoly(
        self,
        coords: list[tuple[int, int]],
        fill: tuple[int, int, int, int] | str = "black",
    ) -> None:
        """Draws a polygon according to its relative position (in range [0-1] for both x and y)

        Args:
            coords (list[tuple[int, int]]): list of relative coordinates
            fill (tuple[int, int, int, int] | str, optional): Fill color. Defaults to "black".
        """
        self._draw.polygon(coords, width=0, fill=fill)

    def _drawMultiplePoly(
        self,
        coords: list[tuple[int, int]],
        fill: tuple[int, int, int, int] | str = "black",
    ) -> None:
        """Draws multiple polygon from list of relative positions (in range [0-1] for both x and y)

        Args:
            coords (list[tuple[int, int]]): list of relative coordinates
            fill (tuple[int, int, int, int] | str, optional): Fill color. Defaults to "black".
        """
        for c in coords:
            abs_coords = self._relativeToAbsolute(c)

            if len(abs_coords) < 3:
                continue

            self._drawPoly(abs_coords, fill)

    def _relativeToAbsolute(self, rel: tuple[float, float]) -> tuple[float, float]:
        if isinstance(rel, tuple):
            return tuple(
                self._border[x] + rel[x] * self._sizes[x] * self._scl for x in [0, 1]
            )

        return list(
            tuple(self._border[x] + r[x] * self._sizes[x] * self._scl for x in [0, 1])
            for r in rel
        )

    def save(self, filename: str) -> None:
        """Saves image as a png file

        Args:
            filename (str): Filename. Extension gets automatically added.
        """
        if filename[-4:] != ".png":
            filename += ".png"

        #! FIX this is bad BUT it works
        out_img = self._image.rotate(90)
        out_img.save(filename, "PNG")

    def drawTrees(self, pos: list[tuple[float, float]]) -> None:
        self._drawMultipleCircles(pos, 1, "darkgreen")

    def drawWater(self, pos: list[tuple[float, float]]) -> None:
        self._drawMultiplePoly(pos, "blue")

    def drawParks(self, pos: list[tuple[float, float]]) -> None:
        self._drawMultiplePoly(pos, "lightgreen")

    def drawBuildings(self, pos: list[tuple[float, float]]) -> None:
        self._drawMultiplePoly(pos, "brown")
