from re import L
from PIL import Image, ImageDraw, ImageFont


class CityImage:
    def __init__(
        self,
        width: int = 2000,
        height: int = 2000,
        background_color: tuple[float, float, float] | str = (240, 240, 240),
        scl: float = 0.8,
        supersample: float = 8,
    ):

        self._supersample = supersample
        self._sizes = (width * self._supersample, height * self._supersample)
        self._scl = scl

        self._border_rations = [0.5, 0.75]
        self._border = tuple(
            self._sizes[x] * (1 - self._scl) * self._border_rations[x] for x in range(2)
        )

        self._image = Image.new("RGB", self._sizes, background_color)
        self._draw = ImageDraw.Draw(self._image)

    def drawCircle(
        self,
        coords: tuple[int, int],
        radius: float = 1,
        fill: tuple[int, int, int] | str = "black",
    ) -> None:
        """Draws a circle according to its relative position (in range [0-1] for both x and y)

        Args:
            coords (tuple[int, int]): circle center coordinates
            radius (float, optional): Circle radius. Defaults to 1.
            fill (tuple[int, int,  int] | str, optional): Fill color. Defaults to "black".
        """
        # arc bounding box
        xy = (
            coords[0] - radius,
            coords[1] - radius,
            coords[0] + radius,
            coords[1] + radius,
        )

        self._draw.ellipse(xy, fill=fill)

    def drawMultipleCircles(
        self,
        coords: list[tuple[int, int]],
        radius: float = 1,
        fill: tuple[int, int, int] | str = "black",
    ) -> None:
        """Draws multiple circles from a list of relative positions (in range [0-1] for both x and y)

        Args:
            coords (tuple[int, int]): circle center coordinates
            radius (float, optional): Circle radius. Defaults to 1.
            fill (tuple[int, int,  int] | str, optional): Fill color. Defaults to "black".
        """

        for c in coords:
            abs_coords = self._relativeToAbsolute(c)
            self.drawCircle(abs_coords, radius, fill)

    def drawPoly(
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

    def drawMultiplePoly(
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

            self.drawPoly(abs_coords, fill)

    def _relativeToAbsolute(
        self, rel: tuple[float, float] | list[tuple[float, float]]
    ) -> list[tuple[float, float]]:
        """Converts relative coordinates to absolute coordinates

        Args:
            rel (tuple[float, float] | list[tuple[float, float]]): list of relative coordinates

        Returns:
            list[tuple[float, float]]: List of absolute coordinates
        """
        if isinstance(rel, tuple):
            return tuple(
                self._border[x] + rel[x] * self._sizes[x] * self._scl for x in range(2)
            )

        return list(
            tuple(self._border[x] + r[x] * self._sizes[x] * self._scl for x in range(2))
            for r in rel
        )

    def addTitle(self, title: str) -> None:
        """Draws a title on the image

        Args:
            text (str): Title text
        """
        size = int((1 - self._scl) * self._sizes[0] * 0.4)
        dy = int((1 - self._scl) * self._sizes[1] * 0.25)
        dx = self._sizes[0] // 2

        font = ImageFont.truetype("src/Chivo-Light.ttf", size)
        fill = (24, 24, 24)

        self._draw.text(
            (dx, dy),
            title,
            fill=fill,
            font=font,
            align="center",
            anchor="mt",
        )

    def save(self, filename: str) -> None:
        """Saves image as a png file

        Args:
            filename (str): Filename. Extension gets automatically added.
        """
        if filename[-4:] != ".png":
            filename += ".png"

        real_size = tuple(int(self._sizes[x] / self._supersample) for x in range(2))
        out_img = self._image.resize(real_size, resample=Image.ANTIALIAS)
        out_img.save(filename, "PNG")

    def drawTrees(self, pos: list[tuple[float, float]]) -> None:
        self.drawMultipleCircles(pos, 2, (16, 16, 16))

    def drawWater(self, pos: list[tuple[float, float]]) -> None:
        self.drawMultiplePoly(pos, (24, 24, 24))

    def drawParks(self, pos: list[tuple[float, float]]) -> None:
        self.drawMultiplePoly(pos, (200, 200, 200))

    def drawBuildings(self, pos: list[tuple[float, float]]) -> None:
        self.drawMultiplePoly(pos, (16, 16, 16))


class DarkCityImage(CityImage):
    def __init__(self):
        super().__init__(background_color=(15, 15, 15))

    def addTitle(self, title: str) -> None:
        """Draws a title on the image

        Args:
            text (str): Title text
        """
        size = int((1 - self._scl) * self._sizes[0] * 0.25)
        dy = int((1 - self._scl) * self._sizes[1] * 0.25)
        dx = self._sizes[0] // 2

        font = ImageFont.truetype("src/Chivo-Light.ttf", size)
        fill = (225, 225, 225)

        self._draw.text(
            (dx, dy),
            title,
            fill=fill,
            font=font,
            align="center",
            anchor="mt",
        )
