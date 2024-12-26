import csv
from flask import Flask, request, jsonify, render_template
from shapely.geometry import Polygon, Point

app = Flask(__name__)

# Carregar os polígonos de um arquivo CSV
poligonos = []
with open('poligonos.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        poligonos.append({
            "nome": row["nome"],
            "coordenadas": eval(row["coordenadas"]),
            "cor": row["cor"]
        })

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/verificar-ponto', methods=['POST'])
def verificar_ponto():
    data = request.get_json()
    ponto_teste = data.get('ponto_teste')
    ponto_id = data.get('ID')

    if not ponto_teste or not ponto_id:
        return jsonify({"error": "ID e ponto_teste são obrigatórios."}), 400

    ponto = Point(ponto_teste)

    for poligono in poligonos:
        poligono_obj = Polygon(poligono["coordenadas"])
        if poligono_obj.contains(ponto):
            return jsonify({
                "ID": ponto_id,
                "ponto_teste": ponto_teste,
                "status": "IN",
                "poligono": poligono["nome"]
            })

    return jsonify({
        "ID": ponto_id,
        "ponto_teste": ponto_teste,
        "status": "OUT",
        "poligono": "null"
    })

@app.route('/visualizar-poligonos')
def visualizar_poligonos():
    return render_template('map.html', poligonos=poligonos)

if __name__ == '__main__':
    app.run(debug=True)
