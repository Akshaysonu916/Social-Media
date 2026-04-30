# train_generative.py
import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, Embedding
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle

# === CONFIGURATION ===
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot")
INTENTS_FILE = os.path.join(DATA_DIR, "intents.json")
MODEL_FILE = os.path.join(DATA_DIR, "gen_chatbot_model.keras")
TOKENIZER_FILE = os.path.join(DATA_DIR, "tokenizer.pkl")
METADATA_FILE = os.path.join(DATA_DIR, "gen_metadata.json")

def train():
    print("Starting Generative AI Training...")
    
    # 1. Load Data
    with open(INTENTS_FILE, 'r') as f:
        intents = json.load(f)
    
    questions = []
    answers = []
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            for response in intent['responses']:
                questions.append(pattern.lower())
                # Add <START> and <END> tokens for the decoder
                answers.append(f"starttoken {response.lower()} endtoken")

    # 2. Tokenization
    tokenizer = Tokenizer(filters='')
    tokenizer.fit_on_texts(questions + answers)
    vocab_size = len(tokenizer.word_index) + 1
    
    # Save Tokenizer
    with open(TOKENIZER_FILE, 'wb') as f:
        pickle.dump(tokenizer, f)

    # 3. Prepare Sequences
    encoder_input_data = tokenizer.texts_to_sequences(questions)
    decoder_input_data = tokenizer.texts_to_sequences(answers)
    
    max_len_q = max(len(x) for x in encoder_input_data)
    max_len_a = max(len(x) for x in decoder_input_data)
    
    encoder_input_data = pad_sequences(encoder_input_data, maxlen=max_len_q, padding='post')
    decoder_input_data = pad_sequences(decoder_input_data, maxlen=max_len_a, padding='post')

    # Decoder target data is same as decoder input but shifted by one
    decoder_target_data = np.zeros((len(answers), max_len_a, vocab_size), dtype='float32')
    for i, seq in enumerate(decoder_input_data):
        for t, word_id in enumerate(seq):
            if t > 0:
                decoder_target_data[i, t-1, word_id] = 1.0

    # 4. Define Seq2Seq Model
    latent_dim = 128
    
    # Encoder
    encoder_inputs = Input(shape=(None,), name="encoder_inputs")
    enc_emb = Embedding(vocab_size, latent_dim, mask_zero=True, name="encoder_embedding")(encoder_inputs)
    encoder_lstm = LSTM(latent_dim, return_state=True, name="encoder_lstm")
    encoder_outputs, state_h, state_c = encoder_lstm(enc_emb)
    encoder_states = [state_h, state_c]

    # Decoder
    decoder_inputs = Input(shape=(None,), name="decoder_inputs")
    dec_emb_layer = Embedding(vocab_size, latent_dim, mask_zero=True, name="decoder_embedding")
    dec_emb = dec_emb_layer(decoder_inputs)
    decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True, name="decoder_lstm")
    decoder_outputs, _, _ = decoder_lstm(dec_emb, initial_state=encoder_states)
    decoder_dense = Dense(vocab_size, activation='softmax', name="decoder_dense")
    decoder_outputs = decoder_dense(decoder_outputs)

    # Compile Model
    model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    
    print("Training the model (this may take a minute)...")
    model.fit([encoder_input_data, decoder_input_data], decoder_target_data, batch_size=32, epochs=200, verbose=1)
    
    # 5. Save Model and Metadata
    model.save(MODEL_FILE)
    
    metadata = {
        "max_len_q": max_len_q,
        "max_len_a": max_len_a,
        "vocab_size": vocab_size
    }
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f)

    print("Generative AI Model trained successfully!")

if __name__ == "__main__":
    train()
