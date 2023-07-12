from flask import Flask, render_template, request, send_file
from youtube_transcript_api import YouTubeTranscriptApi as yta
import requests
from bs4 import BeautifulSoup
import spacy
from googletrans import Translator
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from googletrans.constants import LANGUAGES

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")
translator = Translator()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_link = request.form['video_link']
        dest_lang = request.form['language']

        vid_id = extract_video_id(video_link)

        try:
            data = yta.get_transcript(vid_id)
            transcript = ''
            for value in data:
                for key, val in value.items():
                    if key == 'text':
                        transcript += val
        except:
            transcript = 'Transcript not available.'

        url = f'https://www.youtube.com/watch?v={vid_id}'
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.find('title').get_text()
        desc = soup.find('meta', {'name': 'description'})['content']

        # Tokenizing the text
        stopWords = set(stopwords.words("english"))
        words = word_tokenize(transcript.lower())

        # Creating a frequency table
        freqTable = {word: words.count(word) for word in words if word not in stopWords}

        # Process the transcript using spaCy and extract sentences
        doc = nlp(transcript)
        sentences = [sent.text for sent in doc.sents]

        # Creating a sentence score dictionary
        sentenceValue = {sentence: sum(freqTable.get(word, 0) for word in word_tokenize(sentence.lower()))
                         for sentence in sentences}

        # Calculating the average sentence score
        average = sum(sentenceValue.values()) / len(sentenceValue)

        # Generating the summary
        summary = ''
        for sentence in sentences:
            if sentenceValue[sentence] > (1.2 * average):
                summary += sentence.rstrip()  # Remove trailing whitespace and concatenate sentences

        # Perform translation if summary is not empty and destination language is valid
        if summary:
            if dest_lang in LANGUAGES:
                translation = translator.translate(summary, dest=dest_lang).text
            else:
                translation = 'Invalid destination language.'
        else:
            translation = 'Summary not available.'

        return render_template('index.html', title=title, desc=desc, transcript=translation, translation=translation)

    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    transcript = request.form['transcript']
    title = request.form['title']
    with open('transcript.txt', 'w', encoding='utf-8') as f:
        f.write(transcript)
    return send_file('transcript.txt', as_attachment=True)


def extract_video_id(video_link):
    if 'youtube.com' in video_link:
        video_id = video_link.split('v=')[1]
        if '&' in video_id:
            video_id = video_id.split('&')[0]
    elif 'youtu.be' in video_link:
        video_id = video_link.split('/')[-1]
    else:
        video_id = None
    return video_id

if __name__ == '__main__':
    app.run(debug=True)
