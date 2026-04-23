import re
import nltk
from nltk.corpus import stopwords
import zeyrek

# Download Turkish stopwords if not present
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Initialize Zeyrek Morphological Analyzer (acts as a Python replacement for Zemberek)
analyzer = zeyrek.MorphAnalyzer()
stop_words = set(stopwords.words('turkish'))

def clean_text(text, lowercase=True):
    """
    Cleans raw tweets by removing links, emojis, and specific punctuations.
    """
    if not isinstance(text, str):
        return ""
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove RT and mentions
    text = re.sub(r'RT @\S+:', '', text)
    text = re.sub(r'@\S+', '', text)
    # Remove non-alphanumeric characters (including emojis) except spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower() if lowercase else text

def zemberek_lemmatize(text):
    """
    Applies tokenization and lemmatization to extract root words.
    Uses Zeyrek which is a Python native port of Zemberek.
    """
    cleaned = clean_text(text, lowercase=True)
    words = cleaned.split()
    
    lemmatized_words = []
    for word in words:
        if word in stop_words:
            continue
        try:
            # Zeyrek returns a list of tuples, e.g., [('kelime', ['kök1', 'kök2'])]
            analysis = analyzer.lemmatize(word)
            if analysis and len(analysis) > 0 and len(analysis[0][1]) > 0:
                # Take the first possible root
                root = analysis[0][1][0]
                lemmatized_words.append(root.lower())
            else:
                lemmatized_words.append(word)
        except Exception:
            lemmatized_words.append(word)
            
    return " ".join(lemmatized_words)

if __name__ == "__main__":
    # Test
    sample = "Acil yardım!! Avcılar Merkez mahallesi bina çöktü, insanlar enkaz altında koşuyorlar http://link.com"
    print("Orijinal:", sample)
    print("Temiz:", clean_text(sample))
    print("Zemberek (Kök):", zemberek_lemmatize(sample))
