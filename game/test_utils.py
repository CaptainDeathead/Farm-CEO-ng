from utils import utils
import pygame as pg

pg.init()

screen = pg.display.set_mode((800, 600))

def test_line_collides_mask() -> None:
    line = [(120, 50), (120, 400)]
    multiplyer = 10
    poly = [(2.58*multiplyer, 14.29*multiplyer), (14.39*multiplyer, 14.74*multiplyer), (24.56*multiplyer, 5.94*multiplyer), (14.85*multiplyer, 6.7*multiplyer), (9.63*multiplyer, 12.27*multiplyer), (1.17*multiplyer, 9.01*multiplyer)]

    surf = pg.Surface((800, 600), pg.SRCALPHA)
    pg.draw.polygon(surf, (255, 0, 0), poly)

    screen.blit(surf, (0, 0))
    pg.draw.line(screen, (0, 255, 0), line[0], line[1])

    mask = pg.mask.from_surface(surf)
    poly_rect = utils.get_polygon_rect(poly)

    collide_points = utils.line_collides_mask(line, mask, pg.Rect(0, 0, 0, 0))

    for point in collide_points:
        screen.set_at(point, (0, 0, 255))

    print(f"Polygon rect: {poly_rect}")
    print(f"Line collides mask: {collide_points}")
    print(utils.lines_form_points(collide_points))

def test_shrink_polygon() -> None:
    multiplyer = 10
    poly = [(2.58*multiplyer, 14.29*multiplyer), (14.39*multiplyer, 14.74*multiplyer), (24.56*multiplyer, 5.94*multiplyer), (14.85*multiplyer, 6.7*multiplyer), (9.63*multiplyer, 12.27*multiplyer), (1.17*multiplyer, 9.01*multiplyer)]

    new_poly = utils.shrink_polygon(poly, 10)

    pg.draw.polygon(screen, (255, 255, 255), new_poly)

    print(poly[0], new_poly[0])

if __name__ == "__main__":
    test_line_collides_mask()
    test_shrink_polygon()

    while 1:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                break

        pg.display.flip()