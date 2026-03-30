import io
import ezdxf
from flask import Flask, request, send_file
from ezdxf.enums import TextEntityAlignment

app = Flask(__name__)

# Rozmiary DIN
DIN_SIZES = {
    "a4": (297, 210), "a3": (420, 297), "a2": (594, 420),
    "a1": (841, 594), "a0": (1189, 841)
}

MARGIN = {"left": 25, "right": 10, "top": 10, "bottom": 10}

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json or {}
        size = data.get('size', 'a4').lower().strip()
        
        if size not in DIN_SIZES:
            return {"error": f"Size {size} not supported"}, 400

        width, height = DIN_SIZES[size]
        doc = ezdxf.new(dxfversion="R2010")
        doc.header["$INSUNITS"] = 4  # mm
        msp = doc.modelspace()

        # Rysowanie obramowania zewnętrznego
        msp.add_lwpolyline([(0, 0), (width, 0), (width, height), (0, height)], close=True)

        # Rysowanie ramki wewnętrznej
        fx, fy = MARGIN["left"], MARGIN["bottom"]
        fw, fh = width - MARGIN["left"] - MARGIN["right"], height - MARGIN["top"] - MARGIN["bottom"]
        msp.add_lwpolyline([(fx, fy), (fx + fw, fy), (fx + fw, fy + fh), (fx, fy + fh)], close=True)

        # Tabliczka rysunkowa (uproszczona dla testu)
        tb_w, tb_h = 180, 55
        tx, ty = fx + fw - tb_w, fy
        msp.add_lwpolyline([(tx, ty), (fx + fw, ty), (fx + fw, ty + tb_h), (tx, ty + tb_h)], close=True)
        msp.add_text(f"SIZE: {size.upper()}", dxfattribs={"height": 5}).set_placement((tx + 5, ty + 5))

        # Zapis do strumienia (pamięci RAM)
        out_stream = io.StringIO()
        doc.write(out_stream)
        
        mem = io.BytesIO()
        mem.write(out_stream.getvalue().encode('utf-8'))
        mem.seek(0)

        return send_file(
            mem,
            mimetype="application/dxf",
            as_attachment=True,
            download_name=f"template_{size}.dxf"
        )
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run()
