from flask import Blueprint, render_template, request, jsonify
from random import randint
from transformer.layers import translate
import torch

home = Blueprint('home', __name__)
model = torch.load('model.h5', map_location=torch.device('cpu'))

@home.route('/api', methods=['POST'])
def api():
    try:
        r = request.json['text']
        if len(r) > 1000:
            return jsonify({'error': 'Text too long!'}), 400
        teks, ts, td = translate([r], model)
        return jsonify({'text': r, 'result': teks[0], 'encoded': ts, 'decoded': td})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@home.route('/home')
@home.route('/', methods=['GET', 'POST'])
def homepage():
    return render_template('home.html', title='Home')


@home.route('/about')
def about():
    return render_template('about.html', title='About')
