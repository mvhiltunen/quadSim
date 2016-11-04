
import math
from OpenGL.GL import *

def drawMachine(HORIZONTAL_MOVE, draw_info, hull, mainmotor, sidemotor):
    pos, ax_angle = draw_info["hull_pos"], draw_info["hull_ax_angle"]
    ax0, angle0 = ax_angle

    glPushMatrix()
    glTranslate(pos[0] * HORIZONTAL_MOVE, pos[1] * HORIZONTAL_MOVE, pos[2])

    glPushMatrix()
    glRotate(angle0, ax0[0], ax0[1], ax0[2])
    glCallList(hull.gl_list)
    # glCallList(stick_obj.gl_list)
    glPopMatrix()

    glPushMatrix()
    e_pos, e_ax_angle = draw_info["E1_pos"], draw_info["E1_ax_angle"]
    e_axis = e_ax_angle[0]
    e_angle = e_ax_angle[1]
    glTranslate(e_pos[0] * 2, e_pos[1] * 2, e_pos[2] * 2)
    glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
    glCallList(mainmotor.gl_list)
    # glCallList(stick_obj.gl_list)
    glPopMatrix()

    glPushMatrix()
    e_pos, e_ax_angle = draw_info["E2_pos"], draw_info["E2_ax_angle"]
    e_axis = e_ax_angle[0]
    e_angle = e_ax_angle[1]
    glTranslate(e_pos[0] * 2, e_pos[1] * 2, e_pos[2] * 2)
    glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
    glCallList(mainmotor.gl_list)
    # glCallList(stick_obj.gl_list)
    glPopMatrix()

    glPushMatrix()
    e_pos, e_ax_angle = draw_info["E3_pos"], draw_info["E3_ax_angle"]
    e_axis = e_ax_angle[0]
    e_angle = e_ax_angle[1]
    glTranslate(e_pos[0] * 2, e_pos[1] * 2, e_pos[2] * 2)
    glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
    glCallList(sidemotor.gl_list)
    # glCallList(stick_obj.gl_list)
    glPopMatrix()

    glPushMatrix()
    # e_pos, e_ax_angle = machine.get_engine_pos_and_ax_angle(4)
    e_pos, e_ax_angle = draw_info["E4_pos"], draw_info["E4_ax_angle"]
    e_axis = e_ax_angle[0]
    e_angle = e_ax_angle[1]
    glTranslate(e_pos[0] * 2, e_pos[1] * 2, e_pos[2] * 2)
    glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
    glCallList(sidemotor.gl_list)
    # glCallList(stick_obj.gl_list)
    glPopMatrix()

    glPopMatrix()


def drawFloor(tile, R, tile_r, pos_x, pos_y):
    tile_sep = tile_r * 1.1
    c30 = math.cos(0.5235987755)
    s30 = math.sin(0.5235987755)
    glPushMatrix()
    offset_x = pos_x % (2 * tile_sep * c30)
    offset_y = pos_y % (2 * tile_sep * s30)
    glTranslate(offset_x, offset_y, 0)
    floor_r_i = int(R * 1.6)
    floor_r_j = int(R * 1.6)
    for i in range(-floor_r_i, floor_r_i):
        for j in range(-floor_r_j, floor_r_j):
            i2 = int(i / 2.0)
            ic = i - i2
            j2 = int(j / 2.0)
            jc = j - j2
            os = abs(i % 2)

            x = (ic * tile_sep * c30) + (i2 * tile_sep * c30)
            y = (jc * tile_sep) + os * tile_sep * s30

            if math.sqrt(x * x + y * y) < (R * tile_r):
                glPushMatrix()
                glTranslate(x, y, 0)
                glCallList(tile.gl_list)
                glPopMatrix()
    glPopMatrix()