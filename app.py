from flask import Flask, request, jsonify
from skyfield.api import load, Star, Angle, Topos
from skyfield.data import hipparcos

app = Flask(__name__)

# Constellation to HIP ID mapping
CONSTELLATION_HIP = {
    "aquila":       97649,   # Altair
    "bootes":       69673,   # Arcturus
    "canis_major":  32349,   # Sirius
    "canis_minor":  37279,   # Procyon
    "cassiopeia":   8886,    # Schedar
    "cygnus":      102098,   # Deneb
    "gemini":       36850,   # Pollux
    "leo":          49669,   # Regulus
    "lyra":         91262,   # Vega
    "orion":        24436,   # Betelgeuse
    "pleiades":     17702,   # Alcyone
    "sagittarius":  90185,   # Kaus Australis
    "scorpius":     85927,   # Antares
    "taurus":       21421,   # Aldebaran
    "ursa_major":   54061,   # Dubhe
}

# Load Hipparcos dataset once
with load.open(hipparcos.URL) as f:
    stars = hipparcos.load_dataframe(f)

# Load timescale and ephemeris
ts = load.timescale()
eph = load('de421.bsp')
earth = eph['earth']


def constellation(lat, lon, constellations) -> list:
    output_list = []
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    t = ts.now()

    for const in constellations:
        if const not in CONSTELLATION_HIP:
            output_list.append({"constellation": const, "error": "Unknown constellation"})
            continue

        HIP_ID = CONSTELLATION_HIP[const]
        row = stars.loc[HIP_ID]

        star = Star(
            ra_hours=row['ra_degrees'] / 15.0,  # RA must be in hours
            dec=Angle(degrees=row['dec_degrees'])
        )

        topocentric = observer.at(t)
        astrometric = topocentric.observe(star).apparent()
        alt, az, _ = astrometric.altaz()

        output_list.append({
            "constellation": const,
            "altitude_deg": alt.degrees,
            "azimuth_deg": az.degrees
        })

    return output_list


@app.route("/constellation", methods=["GET"])
def get_constellation():
    """
    Example call:
    /constellation?lat=49.8876&lon=-119.4932&names=leo,lyra,orion
    """
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    names = request.args.get("names", "")

    if lat is None or lon is None or not names:
        return jsonify({"error": "Missing parameters. Use lat, lon, names"}), 400

    constellations = [n.strip().lower() for n in names.split(",")]
    result = constellation(lat, lon, constellations)

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)