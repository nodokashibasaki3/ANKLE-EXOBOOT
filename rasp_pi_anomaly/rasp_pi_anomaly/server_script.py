import prediction_models as pred_utils
from tensorflow import keras
import dl_util
import tcpip as tp
import numpy as np

class JetsonInterface():

    def __init__(self, do_set_up_server=True, server_ip='192.168.1.2', recv_port=8080):
        if do_set_up_server:
            self.servertcp = tp.ServerTCP(server_ip, recv_port)
            self.servertcp.start_server()
        self.gp_sp_isp_dataset = np.array([])
        self.velocity_dataset = np.array([])
        self.ramp_dataset = np.array([])
        self.count = 0

    def load_models(self):
        if self.uni_bi_gp_sp_isp == '1': 
            self.gp_sp_isp_model = keras.models.load_model('gp_sp_isp_unilateral_estimator_model.h5')
        else:
            self.gp_sp_isp_model = keras.models.load_model('gp_sp_isp_bilateral_estimator_model.h5')
        if self.uni_bi_velocity == '1': 
            self.velocity_model = keras.models.load_model('velocity_unilateral_estimator_model.h5')
        else:
            self.velocity_model = keras.models.load_model('velocity_bilateral_estimator_model.h5')
        if self.uni_bi_ramp == '1': 
            self.ramp_model = keras.models.load_model('ramp_unilateral_estimator_model.h5')
        else:
            self.ramp_model = keras.models.load_model('ramp_bilateral_estimator_model.h5')

        self.gp_sp_isp_effective_window = self.get_effective_window(self.gp_sp_isp_model)
        self.ramp_effective_window = self.get_effective_window(self.ramp_model)
        self.velocity_effective_window = self.get_effective_window(self.velocity_model)
        
    def get_effective_window(self, model):
        conv_layer_count = 0

        for layer in model.layers:
            if isinstance(layer, keras.layers.Conv1D):
                kernel_size = layer.kernel_size[0]
                conv_layer_count += 1

        effective_window = kernel_size**conv_layer_count

        return effective_window

    def get_client_message(self):
        self.message = self.servertcp.from_client()

    def unpack_message(self):
        self.message = self.message.split('!')[1:]
        self.get_gp_sp_isp_features, self.uni_bi_gp_sp_isp = self.prep_features(self.message[0])
        self.get_velocity_features, self.uni_bi_velocity = self.prep_features(self.message[1])
        self.get_ramp_features, self.uni_bi_ramp = self.prep_features(self.message[2])

    def prep_features(message):
        features_list = message.split(',')
        features = np.asarray([float(feature) for feature in features_list[:-2]])
        uni_bi = int(features_list[-1])

        return features, uni_bi

    def predict_gp_sp_isp_velocity_ramp(self):
        self.gp_sp_isp_dataset = np.append(self.gp_sp_isp_dataset, self.get_gp_sp_isp_features)[:-self.gp_sp_isp_effective_window,:]
        self.velocity_dataset = np.append(self.velocity_dataset, self.get_velocity_features)[:-self.velocity_effective_window,:]
        self.ramp_dataset = np.append(self.ramp_dataset, self.get_ramp_features)[:-self.ramp_effective_window,:]

        if self.count >= self.gp_sp_isp_effective_window:
            self.gp_sp_isp_predictions = self.gp_sp_isp_model(self.gp_sp_isp_dataset[np.newaxis, :, :])
            self.gp_sp_isp_predictions = self.gp_sp_isp_predictions.reshape(-1, self.gp_sp_isp_predictions.shape[-1])
            self.gait_phase = self.gp_sp_isp_predictions[:,0][0]
            self.stance_phase = self.gp_sp_isp_predictions[:,0][1] 
            self.is_stance_phase = self.gp_sp_isp_predictions[:,0][2]
        if self.count >= self.velocity_effective_window:
            self.velocity_predictions = self.velocity_model(self.velocity_dataset[np.newaxis, :, :])
            self.velocity_predictions = self.velocity_predictions.reshape(-1, self.velocity_predictions.shape[-1])
            self.velocity = self.velocity_predictions[:,0][0]
        if self.count >= self.ramp_effective_window:
            self.ramp_predictions = self.ramp_model(self.ramp_dataset[np.newaxis, :, :])
            self.ramp_predictions = self.ramp_predictions.reshape(-1, self.ramp_predictions.shape[-1])
            self.ramp = self.ramp_predictions[:,0][0]
        
        self.count += 1

    def package_and_send_message(self):
        message = '!' + str(self.gait_phase) + ',' + str(self.stance_phase) + ',' + str(self.is_stance_phase) + \
                  '!' + str(self.velocity) + '!' + str(self.ramp) 
        self.clienttcp.to_server(msg=message)

if __name__ == "__main__":
    print("Starting Server...")
    jetson = JetsonInterface(server_ip='169.254.103.216', recv_port=10000)
    jetson.load_models()

    while True:
        try:
            jetson.get_client_message()
            jetson.unpack_message()
            jetson.predict_gp_sp_isp_velocity_ramp()
            jetson.package_and_send_message()
        except KeyboardInterrupt:
            print('Ctrl-C detected, Exiting Loop!')
            break
    
    jetson.close()
    print('Server Closed!')
