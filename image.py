from PIL import Image, ImageDraw


class ImageCreator:
    def __init__(self, width: int = 2000, height: int = 2000):
        self._width = width
        self._height = height

        self._image = Image.new("RGB", (self._width, self._height), "lightgrey")
        self._draw = ImageDraw.Draw(self._image)

    def _calculateBorder(
        self, relative_points: list[tuple[float, float]]
    ) -> tuple[float, float]:
        """Calculates x, y displacement according to a set of points normalized coords

        Args:
            relative_points (list[tuple[float, float]]): List of relative coordinates

        Returns:
            tuple[float, float]: x and y border on output image
        """

        dx = max(p[0] for p in relative_points) - min(p[0] for p in relative_points)
        dy = max(p[1] for p in relative_points) - min(p[1] for p in relative_points)

        return (1 - dx) / 2, (1 - dy) / 2

    def drawCircle(
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

    def _drawCircle(
        self,
        pos: list[tuple[float, float]],
        fill: tuple[float, float, float, float] | str = None,
        radius: float = 1,
    ) -> None:

        if not fill:
            fill = (0, 0, 0, 255)

        dx, dy = self._calculateBorder(pos)
        size = min(self._width, self._height)

        for p in pos:
            real_pos = (size * (p[0] + dx), size * (p[1] + dy))
            self.drawCircle(real_pos, radius, fill)

    def save(self, filename: str) -> None:
        """Saves image as a png file

        Args:
            filename (str): Filename. Extension gets automatically added.
        """
        if filename[-4:] != ".png":
            filename += ".png"

        self._image.save(filename, "PNG")

    def drawNodes(self, pos: list[tuple[float, float]]) -> None:
        self._drawCircle(pos, "darkgreen", 1)
