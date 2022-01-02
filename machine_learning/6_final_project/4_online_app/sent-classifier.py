from flask import Flask, request, render_template
import pickle
import flask_bootstrap
import numpy as np

app = Flask(__name__, template_folder="html")

print('Loading model ... ', end='')
with open('model/classifier.pickle', 'rb') as input_file:
    cls = pickle.load(input_file)
print('done')


@app.route('/')
@app.route('/index')
def home():
    #hide result pane
    params = {'result_visible': 'is-invisible'}
    return render_template('index.html', **params)  # Render home.html

@app.route('/classify', methods=['POST', 'GET'])
def classify():
    review = request.args.get('review')
    probs = cls.predict_proba([review])[0]
    sent_class = np.argmax(probs)
    prob = round(probs[sent_class] * 100, 2)
    label = ['negative', 'positive'][sent_class]
    params = {'review': review, 'prob': prob, 'label': label}
    return render_template('index.html', **params)


if __name__ == '__main__':
    app.run(debug=False)
