from PIL import Image, ImageDraw


class ImageCreator:
    def __init__(self, width: int = 2000, height: int = 2000, scl: float = 1):
        self._sizes = (width, height)
        self._scl = scl
        self._border = tuple(s * (1 - self._scl) / 2 for s in self._sizes)

        self._image = Image.new("RGB", self._sizes, "lightgrey")
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

    def _drawPoly(
        self,
        coords: list[tuple[int, int]],
        width: float = 1,
        fill: tuple[int, int, int, int] | str = "black",
    ) -> None:
        """Draws a polygon according to its relative position (in range [0-1] for both x and y)

        Args:
            coords (list[tuple[int, int]]): list of relative coordinates
            width (float): line width. Defaults to 1;
            fill (tuple[int, int, int, int] | str, optional): Fill color. Defaults to "black".
        """
        # arc bounding box
        self._draw.polygon(coords, width=width, fill=fill)

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

        self._image.save(filename, "PNG")

    def drawTrees(self, pos: list[tuple[float, float]]) -> None:
        for p in pos:
            abs_pos = self._relativeToAbsolute(p)
            # print(p, abs_pos)
            self._drawCircle(abs_pos, 1, "darkgreen")

    def drawWater(self, pos: list[tuple[float, float]]) -> None:
        for p in pos:
            abs_pos = self._relativeToAbsolute(p)
            self._drawPoly(abs_pos, 1, "blue")
