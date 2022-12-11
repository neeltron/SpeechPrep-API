from flask import Flask, request
import os
import utils
import requests
from replit import db

app = Flask('app')
db['transcription_url'] = ""
db['audio_url'] = ""
db['response'] = ""

def get_transcripts():
  api_key = os.getenv("AAI_API_KEY")
  header = {
    'authorization': api_key,
    'content-type': 'application/json'
  }
  audio_file = "alpha.mp3"
  upload_url = utils.upload_file(audio_file, header)
  transcript_response = utils.request_transcript(upload_url, header)
  print(transcript_response)
  polling_endpoint = utils.make_polling_endpoint(transcript_response)
  db['transcription_url'] = polling_endpoint
  print(polling_endpoint)
  utils.wait_for_completion(polling_endpoint, header)
  paragraphs = utils.get_paragraphs(polling_endpoint, header)
  audio_url = transcript_response['audio_url']
  print(audio_url)
  db['audio_url'] = audio_url
  return paragraphs

@app.route('/', methods=["POST"])
def hello_world():
  if request.method == 'POST':
    file = request.files['file']
    if file:
      file.save("alpha.mp3")
      paragraphs = get_transcripts()
      print(paragraphs)
      return paragraphs
    else:
      return "no file"


@app.route('/analyze', methods = ["GET"])
def analyze():
  if request.method == "GET":
    headers = {
      "authorization": os.getenv("AAI_API_KEY"),
    }
    endpoint = db['transcription_url']
    response = requests.get(endpoint, headers=headers)
    print(response.json())
    db['response'] = response.json()
    return response.json()

# @app.route('/report', methods = ['GET'])
# def report():
#   text = db['response']['text']
#   return

app.run(host='0.0.0.0', port=8080)
