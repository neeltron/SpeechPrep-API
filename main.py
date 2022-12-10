from flask import Flask, request

app = Flask('app')


@app.route('/', methods=["POST"])
def hello_world():
  if request.method == 'POST':
    file = request.files['file']
    if file:
      file.save("alpha.mp3")
      return "file is here"
    else:
      return "no file"


app.run(host='0.0.0.0', port=8080)
