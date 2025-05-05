import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
transcript = YouTubeTranscriptApi.get_transcript("qYNweeDHiyU", proxies={"http": "http://your-proxy:port", "https": "http://your-proxy:port"})
from urllib.parse import urlparse, parse_qs
from transformers import pipeline
import ssl
import re

# SSL fix
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Load summarizer
summarizer = pipeline("summarization", model="Falconsai/text_summarization")



# Functions
def get_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['youtu.be']:
        return parsed_url.path[1:]
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
        if parsed_url.path.startswith(('/embed/', '/v/')):
            return parsed_url.path.split('/')[2]
    return None

def fetch_transcript(video_url):
    video_id = get_video_id(video_url)
    if not video_id:
        raise Exception("Invalid YouTube URL")
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    full_text = " ".join([item['text'] for item in transcript])
    return full_text

def split_text(text, max_words=500):
    words = text.split()
    for i in range(0, len(words), max_words):
        yield " ".join(words[i:i+max_words])

def summarize_text(text):
    chunks = list(split_text(text, max_words=500))
    summarized_chunks = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
        summarized_chunks.append(summary)
    
    full_summary = " ".join(summarized_chunks)
    sentences = re.split(r'(?<=[.!?]) +', full_summary)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    return sentences

def get_thumbnail_url(video_id):
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

# Streamlit UI setup
st.set_page_config(page_title="QuickFlicks: Video Summarizer", page_icon="🎬", layout="wide")

# Background styling
page_bg_img = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: linear-gradient(135deg, #FFDEE9 0%, #B5FFFC 100%);
    background-size: cover;
}
[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🎬 QuickFlicks</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #444;'>Summarize YouTube Videos Instantly!</h3>", unsafe_allow_html=True)
st.markdown("---")

# Input
video_url = st.text_input("Paste YouTube Video URL:")

if st.button("🚀 Summarize", use_container_width=True):
    if video_url:
        try:
            with st.spinner("Fetching transcript..."):
                transcript = fetch_transcript(video_url)

            with st.spinner("Summarizing..."):
                sentences = summarize_text(transcript)
                video_id = get_video_id(video_url)
                thumbnail_url = get_thumbnail_url(video_id)

                # Layout in columns
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.image(thumbnail_url, caption="📷 Video Thumbnail", use_container_width=True)

                with col2:
                    st.markdown("### 📝 Flashcard Summary")
                    for sentence in sentences:
                        st.markdown(
                            f"""
                            <div style='background-color: #FFD580; padding: 15px; margin: 10px 0;
                            border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                            font-size: 18px; color: #333; text-align: center;'>
                                {sentence}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("⚡ Please paste a YouTube URL.")

