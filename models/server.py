# import libraries
from flask import Flask, request, jsonify
import logging
import random
import time

# import settings
from settings import * # import
# set flask params
app = Flask(__name__)
@app.route("/")
def hello():
    return "Classification example\n"
@app.route('/predict', methods=['GET'])
def predict():
    url = request.args['url']
    app.logger.info("Classifying image %s" % (url),)
    
    #response = requests.get(url)
    #img = open_image(BytesIO(response.content))
    t = time.time() # get execution time
    #pred_class, pred_idx, outputs = learn.predict(img)
    #dt = time.time() - t
    #app.logger.info("Execution time: %0.02f seconds" % (dt))
    #app.logger.info(" %s classified as %s" % (url, pred_class))
    pred_class = "happy"
    return jsonify(pred_class)

if __name__ == '__main__':
    
    app.run(host="0.0.0.0", debug=True, port=PORT)