from flask import Flask, request, send_file
import io
import ezdxf
from ezdxf.enums import TextEntityAlignment

app = Flask(__name__)

DIN_SIZES = {
    "a4": (297, 210),
    "a3": (420, 297),
    "a2": (594, 420),
    "a1": (841, 594),
    "a0": (1189, 841),
}

MARGIN = {"left": 25, "right": 10, "top": 10, "bottom": 10}


def generate_blank_template(size: str):
    size = size.lower().strip()
    if size not in DIN_SIZES:
        raise ValueError(f"Unknown size '{size}'. Use: {', '.join(DIN_SIZES)}")

    width, height = DIN_SIZES[size]

    doc = ezdxf.new(dxfversion="R2010")
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1

    doc.layers.new("BORDER",      dxfattribs={"color": 7})
    doc.layers.new("FRAME",       dxfattribs={"color": 7})
    doc.layers.new("TITLE_BLOCK", dxfattribs={"color": 7})
    doc.layers.new("TEXT",        dxfattribs={"color": 7})

    msp = doc.modelspace()

    msp.add_lwpolyline(
        [(0, 0), (width, 0), (width, height), (0, height)],
        close=True, dxfattribs={"layer": "BORDER", "lineweight": 18},
    )

    fx = MARGIN["left"]
    fy = MARGIN["bottom"]
    fw = width  - MARGIN["left"] - MARGIN["right"]
    fh = height - MARGIN["top"]  - MARGIN["bottom"]

    msp.add_lwpolyline(
        [(fx, fy), (fx + fw, fy), (fx + fw, fy + fh), (fx, fy + fh)],
        close=True, dxfattribs={"layer": "FRAME", "lineweight": 50},
    )

    tb_height, tb_width = 55, 180
    tb_x = fx + fw - tb_width
    tb_y = fy

    msp.add_lwpolyline(
        [(tb_x, tb_y), (fx + fw, tb_y), (fx + fw, tb_y + tb_height), (tb_x, tb_y + tb_height)],
        close=True, dxfattribs={"layer": "TITLE_BLOCK", "lineweight": 50},
    )

    row_heights = [9, 9, 9, 9, 9, 10]
    y = tb_y
    row_y = []
    for rh in row_heights:
        row_y.append(y)
        y += rh
        msp.add_line((tb_x, y), (fx + fw, y), dxfattribs={"layer": "TITLE_BLOCK", "lineweight": 18})

    for co in [60, 120]:
        msp.add_line((tb_x + co, tb_y), (tb_x + co, tb_y + tb_height),
                     dxfattribs={"layer": "TITLE_BLOCK", "lineweight": 18})

    def tb_label(text, x, y, h=2.5):
        msp.add_text(text, dxfattribs={"layer": "TEXT", "height": h}).set_placement(
            (x, y), align=TextEntityAlignment.BOTTOM_LEFT)

    pad = 1.5
    c0, c1, c2 = tb_x + pad, tb_x + 60 + pad, tb_x + 120 + pad

    tb_label("TITLE",    c0, row_y[5] + pad)
    tb_label("DRAWN BY", c0, row_y[4] + pad)
    tb_label("DATE",     c1, row_y[4] + pad)
    tb_label("SCALE",    c2, row_y[4] + pad)
    tb_label("CHECKED",  c0, row_y[3] + pad)
    tb_label("DATE",     c1, row_y[3] + pad)
    tb_label("WEIGHT",   c2, row_y[3] + pad)
    tb_label("APPROVED", c0, row_y[2] + pad)
    tb_label("DATE",     c1, row_y[2] + pad)
    tb_label("MATERIAL", c2, row_y[2] + pad)
    tb_label("DOC. NO.", c0, row_y[1] + pad)
    tb_label("REVISION", c2, row_y[1] + pad)
    tb_label("SHEET",    c0, row_y[0] + pad)
    tb_label("OF",       c1, row_y[0] + pad)
    tb_label(size.upper(), c2, row_y[0] + pad, h=4.0)

    mark = 5
    cx, cy = width / 2, height / 2
    for pos, d in [((cx,0),(0,mark)),((cx,height),(0,-mark)),((0,cy),(mark,0)),((width,cy),(-mark,0))]:
        msp.add_line(pos, (pos[0]+d[0], pos[1]+d[1]), dxfattribs={"layer": "BORDER", "lineweight": 18})

    # ── Return as in-memory bytes (no disk write needed) ──
    stream = io.BytesIO()
    doc.write(stream)
    stream.seek(0)
    return stream


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    size = data.get("size", "a4")
    try:
        stream = generate_blank_template(size)
        return send_file(
            stream,
            mimetype="application/dxf",
            as_attachment=True,
            download_name=f"din_{size.lower()}_template.dxf",
        )
    except ValueError as e:
        return {"error": str(e)}, 400


@app.route("/")
def health():
    return {"status": "ok"}

""
