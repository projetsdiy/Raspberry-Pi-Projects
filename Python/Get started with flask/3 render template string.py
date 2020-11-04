from flask import Flask, render_template_string  

app = Flask(__name__) # name for the Flask app (refer to output)

HTML_PAGE = '''
<html>\
   <body>\
     <strong>My First Flask App</strong>\
   </body>\
</html>
'''

@app.route("/") 
def home(): 
    # returning a response
    return render_template_string(HTML_PAGE)

app.run(debug = True)

