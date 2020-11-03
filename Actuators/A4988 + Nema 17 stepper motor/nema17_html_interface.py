#! /usr/bin/python
# -*- coding:utf-8 -*-
# How to drive a Nema 17 stepper motor with the RpiMotorLib Python library for A4988
# Tutorial https://diyprojects.io/drive-nema-17-stepper-motor-rpimotorlib-python-library-a4988/
# Tutoriel https://projetsdiy.fr/raspberry-pi-piloter-moteur-pas-a-pas-nema-17-librairie-rpimotorlib-python-a4988/
# Licence MIT

from RpiMotorLib import RpiMotorLib
from flask import Flask, render_template_string, redirect, request

#define GPIO pins
GPIO_pins = (14, 15, 18)    # Microstep Resolution MS1-MS3 -> GPIO Pin
direction= 20               # Direction Pin, 
step = 21                   # Step Pin
distance = 80               # Default move 1mm => 80 steps per mm


# Declare an named instance of class pass GPIO pins numbers
mymotortest = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")

app = Flask(__name__)

#HTML Code 

TPL = '''
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

        <!-- Bootstrap CSS -->
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">

        <title>Stepper Motor Controller</title>
    </head>
    <body>
      <div class="container">
        <div class="row" style="padding:10">
          <div class="col-sm-1">
            <form method="POST" action="up" class="center-block">
                <button type="submit" class="btn btn-primary">Up</button>
            </form>
          </div>
          <div class="col-sm-1">
            <form method="POST" action="down" class="center-block">
                <button type="submit" class="btn btn-primary">Down</button>
            </form>
          </div> 
        </div>   
            <form method="POST" action="setdistance">
                <div class="btn-group" role="group" >
                  <button name="distance" type="submit" class="btn btn-secondary" value="8">0.1 mm</button>
                  <button name="distance" type="submit" class="btn btn-secondary" value="80">1 mm</button>
                  <button name="distance" type="submit" class="btn btn-secondary" value="800">10 mm</button>
                </div>
            </form>  
        
      </div>   
    </body>
</html>

'''
 
@app.route("/")
def home():
    return render_template_string(TPL)

@app.route("/setdistance", methods=["POST"])
def setdistance():
    global distance
    global distance
    distance = int(request.form["distance"])
    print("set distance to", distance)
    return redirect(request.referrer)
     
@app.route("/up", methods=["POST"])
def up():
    global distance
    print("Move up,", distance, "steps")
    mymotortest.motor_go(False, "Full" , distance, 0.01 , False, .05)
    return redirect(request.referrer)

@app.route("/down", methods=["POST"])
def down():
    global distance
    print("Move down,", distance, "steps")
    mymotortest.motor_go(True, "Full" , distance, 0.01 , False, .05)
    return redirect(request.referrer)
 
# Run the app on the local development server
if __name__ == "__main__":
    app.run()