from sklearn import linear_model
import numpy as np
import math as mt
from tensorflow import keras
import tensorflow as tf
from keras import optimizers
from tensorflow.keras.models import Sequential
from tensorflow.keras.metrics import MeanSquaredError
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.metrics import RootMeanSquaredError
from tensorflow import keras
from tensorflow.keras.layers import InputLayer, LSTM, Dense
from keras.models import Sequential, Model
from keras.layers import Dense, Input, Conv1D, Dropout
from keras.layers import LSTM
from keras.callbacks import ModelCheckpoint
import tensorflow as tf

def get_tcn_model(features, num_conv_layers=5, num_filters=50, kernel_size=4, number_of_dense_layers=3):
    filters = [num_filters]*num_conv_layers
    dilations=[]
    for i in range(num_conv_layers):
        dilations.append(kernel_size**i)
    effective_window = kernel_size**num_conv_layers
    print("Input Sequence Length should be greater than or equal to ",effective_window)
    inputs = Input(shape=(None, features))
    # stack of 1D convolutional layers with increasing dilation rates
    x = inputs
    for i in range(num_conv_layers):
        dilation_rate = dilations[i]
        num_channels = filters[i]
        res_block = Conv1D(filters=num_channels, kernel_size=kernel_size, dilation_rate=dilation_rate, activation=None, padding='causal')(x)
        
        if x.shape[2]!=res_block.shape[2]:
            res_conn = tf.keras.layers.Conv1D(filters=res_block.shape[2], kernel_size=1)(x)
        else:
            res_conn = x
        x = tf.keras.activations.relu(res_block + res_conn)
    
    x = x[:,effective_window-1:,:]
    
    # feedforward layers
    # x = Dense(32, activation='relu')(x)
    # x = Dropout(0.5)(x)
    # x = Dense(16, activation='relu')(x)
    outputs = Dense(number_of_dense_layers, activation=None)(x)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(loss="mse", optimizer="adam", metrics=['mse'])
    return model, effective_window

def gen_checkpoint(checkpoint_filepath = 'TCN_Model_weights/best_weights.h5'):
    checkpoint = ModelCheckpoint(checkpoint_filepath,monitor='val_mse',verbose=1,save_best_only=True,mode='min')
    return checkpoint

def get_lstm_model(features, number_of_dense_layers):
    model = Sequential()
    model.add(InputLayer((None, features)))
    model.add(LSTM(64))
    model.add(Dense(8, activation='relu'))
    model.add(Dense(number_of_dense_layers, activation='linear'))
    model.summary()
    return model