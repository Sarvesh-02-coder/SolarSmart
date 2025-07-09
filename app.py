from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from main import run_model_with_inputs


app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/features")
def features():
    return render_template("features.html")

@app.route("/howItWorks")
def how_it_works():
    return render_template("howItWorks.html")


@app.route("/results")
def results_page():
    return render_template("results.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json
        print("Incoming request:", data)

        result = run_model_with_inputs(
            pincode=data["pincode"],
            material=data["material"],
            manufacturer=data.get("manufacturer", None),
            area=float(data["area"]),
            tilt=float(data.get("tilt", 0))
        )

        print("✅ Prediction complete.")
        return jsonify(result)

    except ValueError as ve:
        print(f"Weather fetch failed (ignored): {ve}")  # for debugging
        return jsonify({}), 200  # Return empty JSON, no error to frontend

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
