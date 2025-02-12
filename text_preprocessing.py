import re
import string
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
STOPWORDS = set(stopwords.words('english'))

def preprocess_text(text):
    """
    Preprocesses input text by:
    - Removing extra whitespace
    - Converting text to lowercase
    - Removing punctuation
    - Removing stopwords
    - Removing numerical values
    """
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove numerical values
    text = re.sub(r'\d+', '', text)
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Remove stopwords
    text = " ".join([word for word in text.split() if word not in STOPWORDS])
    
    return text
