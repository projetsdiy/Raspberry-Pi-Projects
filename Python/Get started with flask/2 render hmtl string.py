from flask import Flask  

app = Flask(__name__) 

@app.route("/") 
def home():
    return "<html>\
              <body>\
                <strong>My First Flask App</strong>\
              </body>\
            </html>"

app.run(debug = True)
