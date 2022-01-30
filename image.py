from PIL import Image, ImageDraw, ImageFont


class ImageCreator:
    def __init__(self, width: int = 2000, height: int = 2000, scl: float = 0.75):
        self._sizes = (width, height)
        self._scl = scl
        self._border = tuple(s * (1 - self._scl) / 2 for s in self._sizes)

        self._image = Image.new("RGB", self._sizes, (220, 220, 220))
        self._draw = ImageDraw.Draw(self._image)

    def _drawCircle(
        self,
        coords: tuple[int, int],
        r: float = 1,
        fill: tuple[int, int, int] | str = "black",
    ) -> None:
        """Draws a circle according to its relative position (in range [0-1] for both x and y)

        Args:
            coords (tuple[int, int]): circle center coordinates
            r (float, optional): Circle radius. Defaults to 1.
            fill (tuple[int, int,  int] | str, optional): Fill color. Defaults to "black".
        """
        # arc bounding box
        xy = (coords[0] - r, coords[1] - r, coords[0] + r, coords[1] + r)

        self._draw.ellipse(xy, fill=fill)

    def _drawMultipleCircles(
        self,
        coords: list[tuple[int, int]],
        r: float = 1,
        fill: tuple[int, int, int] | str = "black",
    ) -> None:
        """Draws multiple circles from a list of relative positions (in range [0-1] for both x and y)

        Args:
            coords (tuple[int, int]): circle center coordinates
            r (float, optional): Circle radius. Defaults to 1.
            fill (tuple[int, int,  int] | str, optional): Fill color. Defaults to "black".
        """

        for c in coords:
            abs_coords = self._relativeToAbsolute(c)
            self._drawCircle(abs_coords, r, fill)

    def _drawPoly(
        self,
        coords: list[tuple[int, int]],
        fill: tuple[int, int, int] | str = "black",
    ) -> None:
        """Draws a polygon according to its relative position (in range [0-1] for both x and y)

        Args:
            coords (list[tuple[int, int]]): list of relative coordinates
            fill (tuple[int, int,  int] | str, optional): Fill color. Defaults to "black".
        """
        self._draw.polygon(coords, width=0, fill=fill)

    def _drawMultiplePoly(
        self,
        coords: list[tuple[int, int]],
        fill: tuple[int, int, int] | str = "black",
    ) -> None:
        """Draws multiple polygon from list of relative positions (in range [0-1] for both x and y)

        Args:
            coords (list[tuple[int, int]]): list of relative coordinates
            fill (tuple[int, int,  int] | str, optional): Fill color. Defaults to "black".
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

    def addTitle(self, text: str) -> None:
        size = int((1 - self._scl) * self._sizes[0] * 0.3)
        pos = tuple(int((1 - self._scl) * self._sizes[x] * 0.1) for x in [0, 1])
        font = ImageFont.truetype("src/Chivo-Light.ttf", size)
        fill = (16, 16, 16)

        self._draw.text(
            pos,
            text,
            fill=fill,
            font=font,
            anchor="lt",
        )

    def rotate(self, angle):
        self._image.rotate(angle)

    def save(self, filename: str) -> None:
        """Saves image as a png file

        Args:
            filename (str): Filename. Extension gets automatically added.
        """
        if filename[-4:] != ".png":
            filename += ".png"

        self._image.save(filename, "PNG")

    def drawTrees(self, pos: list[tuple[float, float]]) -> None:
        self._drawMultipleCircles(pos, 2, (16, 16, 16))

    def drawWater(self, pos: list[tuple[float, float]]) -> None:
        self._drawMultiplePoly(pos, (24, 24, 24))

    def drawParks(self, pos: list[tuple[float, float]]) -> None:
        self._drawMultiplePoly(pos, (128, 128, 128))

    def drawBuildings(self, pos: list[tuple[float, float]]) -> None:
        self._drawMultiplePoly(pos, (16, 16, 16))
