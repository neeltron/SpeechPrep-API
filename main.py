from flask import Flask, request
import os
import utils
import requests
import json
from replit import db

url = "https://dnaber-languagetool.p.rapidapi.com/v2/check"

payload = "language=en-US&text=hi%20this%20is%20a%20test.%20the%20response."
headers2 = {
	"content-type": "application/x-www-form-urlencoded",
	"X-RapidAPI-Key": "8f85d2a172msh6818abcfdc7f541p104edbjsn56569112cb59",
	"X-RapidAPI-Host": "dnaber-languagetool.p.rapidapi.com"
}

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
    score = 10
    headers = {
      "authorization": os.getenv("AAI_API_KEY"),
    }
    endpoint = db['transcription_url']
    response = requests.get(endpoint, headers=headers)
    # print(response.json())
    
    db['response'] = response.json()['text']
    text = str(db['response']).replace(" ", "%20")
    # print(text)
    payload = "language=en-US&text=" + text
    response2 = requests.request("POST", url, data=payload, headers=headers2)
    mistakes = json.loads(response2.text)['matches']
    str_mistakes = ""
    for i in range(0, len(mistakes)):
      str_mistakes += mistakes[i]['message'] + "\n"
      score -= 0.5
    # print(str_mistakes)
    print(response)
    response = response.json()
    sentiment_score = 0
    sentiment = ""
    senti_dict = {'sentiment': 'neutral'}
    sentiment_individual = ""
    for i in range(0, len(response['sentiment_analysis_results'])):
      sentiment = response['sentiment_analysis_results'][i]['sentiment']
      text = response['sentiment_analysis_results'][i]['text']
      sentiment_individual += text + ":" + sentiment + "\n"
      if sentiment == "POSITIVE":
        sentiment_score += 1
      elif sentiment == "NEUTRAL":
        sentiment_score += 0
      else:
        sentiment_score -= 1
    score += sentiment_score/len(response['sentiment_analysis_results'])
    if sentiment_score > 0:
      senti_dict = {'sentiment': 'positive'}
    elif sentiment_score == 0:
      senti_dict = {'sentiment': 'neutral'}
    else:
      senti_dict = {'sentiment': 'negative'}
    safety_label = ""
    for i in range(0, len(response['content_safety_labels']['results'][0]['labels'])):
      safety_label += response['content_safety_labels']['results'][0]['labels'][i]['label'] + "\n"
      score -= 0.5

    safety_label_dict = {"safety_labels": safety_label}
    senti_dict2 = {'individual': sentiment_individual}
    wrap_mistakes = {'mistakes': str_mistakes}
    score_dict = {'score': str(score)}
    merged_dict = {**response, **wrap_mistakes, **senti_dict, **senti_dict2, **safety_label_dict, **score_dict}
    return json.dumps(merged_dict)


app.run(host='0.0.0.0', port=8080)
