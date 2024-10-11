import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os
import argparse


def print_options(is_vnmc_included_in_past_data):
    if is_vnmc_included_in_past_data:
        print("""1: All Acceleration & Gyro Data
2: Motor Angle, Velocity & Current data
3: Ankle Angle, Velocity & Torque from Current Data
4: Did Heel Strike (Boolean), Did Toe Off (Boolean) & gait_phase data
5: Command Current, Position and Torque data
6: Slack & Temperature data
7: Controller Implemented and Control State Data
8: Muscle Tendon Unit (MTU) Length, Velocity, Torque, Force, Muscle Stimulation and Ankle Angle""")
    else:
        print("""1: All Acceleration & Gyro Data
2: Motor Angle, Velocity & Current data
3: Ankle Angle, Velocity & Torque from Current Data
4: Did Heel Strike (Boolean), Did Toe Off (Boolean) & gait_phase data
5: Command Current, Position and Torque data
6: Slack & Temperature data
7: Controller Implemented and Control State Data""")


def get_len_from_seconds(length_1, length_2, past_data_file):
    length_list = []
    for i in [length_1, length_2]:
        for j in range(len(past_data_file)):
            if float(past_data_file['loop_time'][j]) >= float(i):
                length_list.append(j)
                break
            else:
                pass
    length_1 = length_list[0]
    length_2 = length_list[1]

    return length_1, length_2


def get_data_from_input(input_from_user, past_data_file):
    list_of_input = input_from_user.split()
    try:
        if len(list_of_input) == 1:
            choice_of_plot = str(input_from_user)
            length_1 = 0
            length_2 = 5
        elif len(list_of_input) == 2:
            choice_of_plot = str(list_of_input[0])
            length_1 = 0
            length_2 = float(list_of_input[1])
        elif len(list_of_input) == 3:
            choice_of_plot = str(list_of_input[0])
            length_1 = float(list_of_input[1])
            length_2 = float(list_of_input[2])
        elif not list_of_input:
            choice_of_plot, length_1, length_2 = '', None, None
            return length_1, length_2, choice_of_plot
        else:
            choice_of_plot, length_1, length_2 = 'a', None, None
            return length_1, length_2, choice_of_plot
    except:
        print('Input not recognized. Please enter float and integers only.')
        return

    length_1, length_2 = get_len_from_seconds(length_1, length_2, past_data_file)

    return length_1, length_2, choice_of_plot


def plotter(past_data_file):
    loop_choice_of_plot = True

    print('')
    try:
        for find_vnmc in range(len(past_data_file)):
            if past_data_file['controller'][find_vnmc] == "ControllerUsed.VirtualNeuromusuclarController":
                is_vnmc_included_in_past_data = True
                break
            else:
                is_vnmc_included_in_past_data = False
    except:
        is_vnmc_included_in_past_data = False

    print_options(is_vnmc_included_in_past_data)

    while loop_choice_of_plot:
        input_from_user = input(
            '\nWhat data would you like to plot (enter number)? Press Enter to quit.\n> ')
        if input_from_user == '':
            print('Exiting...')
            return
        else:
            length_1, length_2, choice_of_plot = get_data_from_input(input_from_user, past_data_file)
            if choice_of_plot is None:
                continue
            elif choice_of_plot.lower() == 'a':
                print('Input not recognized. Please enter a valid input.')
                continue
            else:
                loop_choice_of_plot = False

    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.02)

    if choice_of_plot == '1':
        fig.add_trace(
            go.Scatter(x=past_data_file['loop_time'][length_1:length_2],
                       y=past_data_file['accelerometer_x'][length_1:length_2],
                       mode='lines',
                       name='Accelerometer X',
                       line=dict(color='blue')),
            row=1, col=1)
        # ... Add other traces for different data columns if needed

    fig.update_layout(title_text='Plot Title', xaxis_title='X Axis', yaxis_title='Y Axis')

    fig.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot data from past and new data files.')
    parser.add_argument('--past', metavar='past_data_file', type=str, help='Path to the past data file')
    args = parser.parse_args()

    if args.past:
        past_data_file_path = args.past
    else:
        past_data_file_path = r'C:\Users\ft700\Documents\Shepherd Lab\Hip Exo Code\Exoboot Code Jayston\Exoboot Code Cleaned Up\Default_Past_Data_LEFT.csv'

    if not os.path.isfile(past_data_file_path):
        print('Past data file not found.')
    else:
        past_data_file = pd.read_csv(past_data_file_path)

        plotter(past_data_file)
