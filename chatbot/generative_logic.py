# chatbot/generative_logic.py
import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, LSTM, Dense, Embedding
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle

# === CONFIGURATION ===
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(DATA_DIR, "gen_chatbot_model.keras")
TOKENIZER_FILE = os.path.join(DATA_DIR, "tokenizer.pkl")
METADATA_FILE = os.path.join(DATA_DIR, "gen_metadata.json")

class ChatbotGenerator:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.metadata = None
        self.encoder_model = None
        self.decoder_model = None
        self.load_resources()

    def load_resources(self):
        try:
            if not os.path.exists(MODEL_FILE):
                return
            
            # Load basic model and metadata
            self.model = load_model(MODEL_FILE)
            with open(TOKENIZER_FILE, 'rb') as f:
                self.tokenizer = pickle.load(f)
            with open(METADATA_FILE, 'r') as f:
                self.metadata = json.load(f)
            
            self.setup_inference_models()
        except Exception as e:
            print(f"Error loading generative models: {e}")

    def setup_inference_models(self):
        try:
            # We need to rebuild the encoder and decoder models for inference
            latent_dim = 128
            
            # Find layers by name first (more precise)
            try:
                encoder_lstm = self.model.get_layer('encoder_lstm')
                decoder_lstm = self.model.get_layer('decoder_lstm')
                dec_emb_layer = self.model.get_layer('decoder_embedding')
                dense_layer = self.model.get_layer('decoder_dense')
            except:
                # Fallback to type check if names not found (for backward compatibility)
                print("Warning: Named layers not found, falling back to type identification...")
                encoder_lstm = None
                decoder_lstm = None
                embeddings = []
                dense_layer = None
                
                for layer in self.model.layers:
                    if isinstance(layer, LSTM):
                        if encoder_lstm is None:
                            encoder_lstm = layer
                        else:
                            decoder_lstm = layer
                    elif isinstance(layer, Embedding):
                        embeddings.append(layer)
                    elif isinstance(layer, Dense):
                        dense_layer = layer
                dec_emb_layer = embeddings[1] if len(embeddings) >= 2 else None

            if not (encoder_lstm and decoder_lstm and dec_emb_layer and dense_layer):
                raise ValueError("Could not find all required layers in the model.")

            # 1. Encoder Inference Model
            encoder_inputs = self.model.input[0]
            _, state_h_enc, state_c_enc = encoder_lstm.output
            encoder_states = [state_h_enc, state_c_enc]
            self.encoder_model = Model(encoder_inputs, encoder_states)

            # 2. Decoder Inference Model
            decoder_inputs = self.model.input[1]
            dec_emb = dec_emb_layer(decoder_inputs)
            
            decoder_state_input_h = Input(shape=(latent_dim,))
            decoder_state_input_c = Input(shape=(latent_dim,))
            decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
            
            decoder_outputs, state_h_dec, state_c_dec = decoder_lstm(
                dec_emb, initial_state=decoder_states_inputs
            )
            decoder_states = [state_h_dec, state_c_dec]
            decoder_outputs = dense_layer(decoder_outputs)
            
            self.decoder_model = Model(
                [decoder_inputs] + decoder_states_inputs,
                [decoder_outputs] + decoder_states
            )
        except Exception as e:
            print(f"Error setting up inference models: {e}")
            self.encoder_model = None
            self.decoder_model = None

    def generate_response(self, text):
        if not self.encoder_model or not self.decoder_model:
            return "My AI brain is still initializing. Please try again in a few seconds."

        # Tokenize and Pad Input
        input_seq = self.tokenizer.texts_to_sequences([text.lower()])
        input_seq = pad_sequences(input_seq, maxlen=self.metadata['max_len_q'], padding='post')

        # Encode the input to get the initial states for the decoder
        states_value = self.encoder_model.predict(input_seq, verbose=0)

        # Generate empty target sequence of length 1 with the start token
        target_seq = np.zeros((1, 1))
        target_seq[0, 0] = self.tokenizer.word_index.get('starttoken', 0)

        stop_condition = False
        decoded_sentence = ""
        
        while not stop_condition:
            output_tokens, h, c = self.decoder_model.predict([target_seq] + states_value, verbose=0)

            # Sample a token
            sampled_token_index = np.argmax(output_tokens[0, -1, :])
            sampled_word = None
            for word, index in self.tokenizer.word_index.items():
                if index == sampled_token_index:
                    sampled_word = word
                    break

            if sampled_word == 'endtoken' or len(decoded_sentence.split()) > self.metadata['max_len_a']:
                stop_condition = True
            elif sampled_word:
                decoded_sentence += " " + sampled_word

            # Update the target sequence (of length 1)
            target_seq = np.zeros((1, 1))
            target_seq[0, 0] = sampled_token_index

            # Update states
            states_value = [h, c]

        return decoded_sentence.strip()
