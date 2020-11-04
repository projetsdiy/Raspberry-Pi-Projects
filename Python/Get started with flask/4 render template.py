from flask import Flask, render_template  

app = Flask(__name__) # name for the Flask app (refer to output)


@app.route("/") 
def home(): 
    # returning a response
    return render_template('test4/page.html')

app.run(debug = True)


