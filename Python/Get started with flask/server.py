from flask import Flask, render_template, redirect, request  

app = Flask(__name__) 

distance = 0.1

@app.route("/") 
def home(): 
    global distance
    return render_template('test8/page.html', distance=distance)

@app.route("/setdistance", methods=["POST"])
def setdistance():
    global distance
    distance = float(request.form["distance"])
    print("set distance to", distance)
    return redirect(request.referrer)   

app.run(debug = True)