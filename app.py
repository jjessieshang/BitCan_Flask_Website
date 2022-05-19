from flask import Flask, redirect, url_for, render_template, request

app = Flask(__name__)

@app.route("/")
def home(): #home page
    return render_template("index.html")

@app.route("/login/", methods=["POST","GET"])
def login():
    if request.method == "POST":
        user = request.form["nm"]
        return redirect(url_for("user", usr=user))
    else:
        return render_template("login.html")

@app.route("/<usr>")
def user(usr):
    return f"<h1>{usr}</h1>"

@app.route("/mapping/")
def mapping(): #mapping page
    start_coords = (55.0, -110)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    return folium_map._repr_html_()


@app.route("/topography/")
def topography(): #topography page
    return render_template("topography.html")

if __name__ == "__main__":
    app.run(debug=True)


    # @app.route("/<name>") #passing as a parameter
# def test(name):
#     return render_template("testy.html", content=name, r=2, list=["Tim","Joe","Bill"])