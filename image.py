from PIL import Image, ImageDraw


class ImageCreator:
    def __init__(self, width: int = 2000, height: int = 2000):
        self._width = width
        self._height = height

        self._image = Image.new("RGB", (self._width, self._height), "lightgrey")
        self._draw = ImageDraw.Draw(self._image)

    def _calculateBorder(
        self, relative_points=list[tuple[float, float]]
    ) -> tuple[float, float]:
        dx = max(p[0] for p in relative_points) - min(p[0] for p in relative_points)
        dy = max(p[1] for p in relative_points) - min(p[1] for p in relative_points)

        return (1 - dx) / 2, (1 - dy) / 2

    def drawCircle(
        self, point: tuple[int, int], r: float, fill: tuple[int, int, int, int]
    ) -> None:
        # draws a point according to its absolute position (in range [0-1] for both x and y)
        # arc bounding box
        xy = (point[0] - r, point[1] - r, point[0] + r, point[1] + r)

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
        if filename[:-4] != ".png":
            filename += ".png"

        self._image.save(filename, "PNG")

    def drawTrees(self, pos: list[tuple[float, float]]) -> None:
        self._drawCircle(pos, "darkgreen", 1)
