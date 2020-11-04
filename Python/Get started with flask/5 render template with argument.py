from flask import Flask, render_template  

app = Flask(__name__) 

@app.route("/") 
def home(): 
    return render_template('test5/page.html', status=True, temperature=21.4)

app.run(debug = True)
