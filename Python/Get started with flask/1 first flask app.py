from flask import Flask  

app = Flask(__name__) # name for the Flask app (refer to output)

@app.route("/") 
def home(): 
    # returning a response
    return "Hello World!"

app.run(debug = True)