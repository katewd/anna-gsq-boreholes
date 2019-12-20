from keras.layers import LSTM, Activation, Dense, Dropout, TimeDistributed, Input, Embedding
from keras.optimizers import RMSprop
from keras.preprocessing.text import Tokenizer
from keras.preprocessing import sequence
from keras.models import load_model
import tensorflow as tf
import joblib
import os
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import LSTM, Dense
from keras.utils import to_categorical
import numpy as np
import pandas as pd
import re
import settings


class NeuralNetwork(): #give this arguments like: model type, train/test file
    #max_words = 900
    #max_len = 15
    #y_dict = {}
    epochs = 10
    batch_size = 50
    tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
    model_path = settings.model_path
    #model_name = 'heading_id_cyfra1'

    def __init__(self, model_name='cyfra1'):
        self.model_name = 'heading_id_' + model_name
        self.model_loc = self.model_path + self.model_name + '.h5'
        self.tok_loc = self.model_path + self.model_name + 'tokeniser.joblib'

    def train(self, file='processed_heading_id_dataset_cyfra1.csv'):
        df = pd.read_csv(file)
        self.X = df['SectionText']
        self.Y = df['Heading']
        self.max_words, self.max_len = check_maxlens(df)
        self.tok = Tokenizer(num_words=self.max_words)
        self.model = self.LSTM() #StackedLSTM()

        X_train, X_test, Y_train, Y_test = train_test_split(self.X, self.Y, test_size=0.15)

        self.tok.fit_on_texts(X_train)
        sequences = self.tok.texts_to_sequences(X_train)
        sequences_matrix = sequence.pad_sequences(sequences, maxlen=self.max_len)
        y_binary = to_categorical(Y_train)
        self.model.summary()
        self.model.fit(sequences_matrix, y_binary, batch_size=self.batch_size, epochs=self.epochs,
                  validation_split=0.2) #, callbacks=[EarlyStopping(monitor='val_loss',min_delta=0.0001)]

        test_sequences = self.tok.texts_to_sequences(X_test)
        test_sequences_matrix = sequence.pad_sequences(test_sequences, maxlen=self.max_len)

        accr = self.model.evaluate(test_sequences_matrix, to_categorical(Y_test))
        print('Test set\n  Loss: {:0.3f}\n  Accuracy: {:0.3f}'.format(accr[0], accr[1]))
        self.model.save(self.model_loc)
        joblib.dump(self.tok, self.tok_loc)


    def StackedLSTM(self):
        # Stacked LSTM for sequence classification from https://keras.io/getting-started/sequential-model-guide/
        model = Sequential()
        model.add(LSTM(32, return_sequences=True, input_shape=self.max_len))
        model.add(LSTM(32, return_sequences=True))
        model.add(LSTM(32))
        model.add(Dense(10, activation='softmax'))
        model.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=['accuracy', 'categorical_accuracy'])
        return model

    def LSTM(self):
        model = Sequential()
        model.add(Embedding(self.max_words, output_dim=256))#self.max_len))
        model.add(LSTM(128))
        model.add(Dropout(0.5))
        model.add(Dense(3, activation='softmax'))

        model.compile(loss='categorical_crossentropy',
                      optimizer='rmsprop',
                      metrics=['accuracy'])
        return model


    def load_model_from_file(self):
        self.model = load_model(self.model_loc)
        self.tok = joblib.load(self.tok_loc)
        self.model._make_predict_function()


    def predict(self, strings):
        if not os.path.exists(self.model_loc):
            self.train()
        try:
            self.model
        except AttributeError:
            self.load_model_from_file()

        #encoded = [num2cyfra1(s) for s in strings]
        sequences = self.tok.texts_to_sequences(strings)
        #self.max_len
        sequences_matrix = sequence.pad_sequences(sequences, maxlen=256)
        predictions = self.model.predict(sequences_matrix)
        return predictions, np.argmax(predictions, axis=1)


def num2cyfra1(string):
    s = ''
    prev_c = ''
    i = 1
    for c in string:
        if re.match(r'[0-9]', c):
            if prev_c != 'num':
                s += 'cyfra' + str(i) + ' '
                i += 1
                prev_c = 'num'
        elif c == '.':
            s += 'punkt '
            prev_c = '.'
        else:
            s+= c
    return s


def check_maxlens(df):
    series = df['SectionText']
    max_len = series.str.len().max()
    words = series.str.lower().str.split().apply(set().update)
    max_words = len(words)
    return max_words, max_len


if __name__ == '__main__':
    data = 'processed_heading_id_dataset_cyfra1.csv'

    nn = NeuralNetwork()
    #nn.train(data)
    nn.load_model_from_file()
    p, r = nn.predict(['4.3 drilling', 'Introduction 1', 'lirowjls', 'figure drilling', '5 . 9 . geology of culture 5', '1 . introduction', '8 . 1 introduction 7'])
        #['4.3 drilling', 'Introduction strona', 'lirowjls', 'figure drilling', '5 . 9 . geology of culture strona', '1 . introduction', '8 . 1 introduction strona'])
    print(p)
    print('------------------')
    print(r)