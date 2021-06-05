"""
Player Object for RCSS.
"""
# imports
import socket
import torch

# ------------------------------------------------------------------------------
class Player:
    """
    """

    def __init__(self, team, goalie=False, ki=False):
        """
        Initialize connection to RCSS.

        team - str: the team of the player (2 teams for one game)
        goalie - bool: the flag if this player is a goalie (defaul,t false)
        ki - bool: decide between normal and ki "brain" of player
        """

        # create instance variable to save what the player sees
        self.see = None
        # instance variable to save what player does in last step
        self.command = ''
        # variable to decide between brains
        self.ki = ki

        # create instance variable pdata (player data)
        self.pdata = dict()
        self.pdata['team'] = team
        self.pdata['goalie'] = goalie

        # create instance variable sdata (server data)
        self.sdata = dict()
        self.sdata['port'] = 6000
        self.sdata['address'] = '192.168.2.116'
        self.sdata['buffer_size'] = 102400

        self.learning_steps = 0

        # create instance variables for ki
        self.obj_mapping = {
                'b': 1,
                'f': 2,
                'p': 3,
                'g': 4,
                'l': 5
            }
        self.cmd_mapping = {
                'kick': 1,
                'turn': 2,
                'dash': 3
            }
        self.cmd_back_mapping = ['kick', 'turn', 'dash']

        # Create a UDP socket at client side
        self.udp_socket = socket.socket(family=socket.AF_INET, \
            type=socket.SOCK_DGRAM)

        # login player at server and write configuration
        self.write_init_config(goalie)

        # TODO: (marker) disable in game mode
        # self.run()

        # KI modell erstellen
        self.model = torch.nn.Sequential(
            torch.nn.Conv1d(3, 3, 1)
        )

        # compute loss
        self.criterion = torch.nn.MSELoss(reduction='sum')

    	# optimizer
        lr = 1e-5
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)

    def run(self):
        """
        Run the player.
        """

        # set loop to work with server
        while True:
            # recive message from server
            msg, _ = self.recive_msg()

            # process sensor data what player is seen
            if 'see' in msg:
                self.process_see(msg)

            # compute player command
            if self.ki:
                # learning

                # if self.learning_steps < 500:
                self.command = self.compute_reaction()
                self.learning_steps += 1
                # compute ki command
                self.command = self.compute_ki_reaction()



            else:
                self.command = self.compute_reaction()

            # send new message to server
            # command = input('Befehl: ')
            self.send_msg(self.command)

    # --------------------------------------------------------------------------
    def process_see(self, see_msg):
        """
        Write a list of all Objects which the user is seen into self.see.

        see_msg - str: the information from the server about the sensor model
        """

        # generate list of all seen objectrs and write to instance variable
        self.see = see_msg.split('(', 2)[-1][:-3].split(') (')

    def write_init_config(self, goalie=False):
        """
        Get the initial config from the server and writes them to the dict.

        goalie - bool: the flag if this player is a goalie (defaul,t false)
        """

        # send initialisation
        msg = "(init {} (version 7){})".format(self.pdata['team'], ' (goalie)' \
            if goalie else '')
        self.send_msg(msg)

        # recive data from server
        msg, server_info = self.recive_msg()

        # set new server port
        self.sdata['port'] = server_info[1]

        # set player id
        player_info = msg.split(' ')
        self.pdata['id'] = player_info[2]
        self.pdata['side'] = player_info[1]
        self.pdata['mode'] = player_info[3][:-2]

        # set player to position 0 0, if possible ;)
        self.send_msg('(move 0 0)')

        # turn player if looking in wrong direction
        change = True
        while True:
            msg, server_info = self.recive_msg()
            if 'see' in msg:
                self.process_see(msg)
                # get all object and check if player sees middle of field
                for target in self.see:
                    object_type, _, _ = self.get_values_from_see(target)
                    # check if player look to middle of field
                    if object_type == 'f c b' or object_type == 'f c' or \
                        object_type == 'f c t':
                        change = False

                break
        # turn player if looking not to middle of field
        if change:
            self.send_msg('(turn 180)')

    def recive_msg(self):
        """
        Recives the content from the RCSS.

        Returns tuple (decoded string, tuple).
        """

        msg = self.udp_socket.recvfrom(self.sdata['buffer_size'])

        return msg[0].decode(), msg[1]

    def send_msg(self, msg):
        """
        Send a given message (msg) to the RCSS.

        msg - str: the message / the command whish should send to the server
        """

        # encode given message and send to server
        self.udp_socket.sendto(str.encode(msg), \
            (self.sdata['address'], self.sdata['port']))

    def compute_reaction(self):
        """
        Computes the reaction of the player.

        Returns sommand for the server (str).
        """

        # get parameter what player is seen
        if self.see is not None:
            out = True

            for target in self.see:
                object_type, distance, direction = self.get_values_from_see( \
                    target)

                try:
                    if object_type[0]  in ['f', 'b', 'p', 'g']:
                        out = False

                except TypeError:
                    return '(dash 50)' if 'dash' not in self.command else \
                        '(turn 20)'

                # compute reaction of seen object
                if object_type == 'b' and float(distance) < 1:
                    return '(kick 100 0)'

                elif object_type == 'b' and 'turn' not in self.command:
                    return '(turn {})'.format(direction)

                elif object_type in ['l b', 'l l', 'l r', 'l t'] and float( \
                    distance) < 10 and 'turn' not in self.command:
                    return '(turn 180)'


        if not out:
            return '(dash 50)' if 'dash' not in self.command else '(turn 20)'


        else:
            return '(turn 100)' if 'turn' not in self.command else \
                '(dash 50)'

    def compute_ki_reaction(self):
        """
        Computes the reaction of the player with CNN.

        Returns sommand for the server (str).
        """

        # get parameter what player is seen
        if self.see is not None:
            out = True
            input_tensor = None

            for target in self.see:
                # get values from sensors
                object_type, distance, direction = self.get_values_from_see( \
                    target)

                # find object type
                torch_obj = ''
                found = False
                try:
                    for obj in self.obj_mapping:
                        if obj in object_type:
                            torch_obj = int(self.obj_mapping[obj])
                            found = True

                except TypeError:
                    torch_obj = 0

                # check if object type is known
                if not found:
                    torch_obj = 0


                if object_type == 'b':
                    input_tensor = torch.tensor([[[float(torch_obj)], \
                        [float(distance)], [float(direction)]]])
                    break

            if input_tensor is not None:
                predicted_value = self.model(input_tensor)

            else:
                return '(turn 10)'

            # create output tensor with values for learning
            # if self.learning_steps < 500:
            action = int(self.cmd_mapping[self.command.split('(')[1].split( \
                ' ')[0]])
            param = float(self.command.split('(')[1].split(' ')[1].split(')')[ \
                0])
            output_tensor = torch.tensor([[[action], [param], [0]]])


        # calculate loss and optimize cnn
        #if self.learning_steps < 500:
        loss = self.criterion(predicted_value, output_tensor) # + REWARD
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if self.pdata['id'] == '1':
            print(loss.item())

        # compute command for rcss
        ki_out = list()
        for out_item in predicted_value:
            for inner_item in out_item:
                ki_out.append(inner_item.item())

        # MAPPING zu entsporechendem Kommando für RCSS

        try:
            command = '({} {})'.format(self.cmd_back_mapping[int(round( \
                ki_out[0] - 1))], int(round(ki_out[1])))
        except IndexError:
            command = ''

        # return ki_command
        if 'kick' in command:
            command = '{} 0)'.format(command.split(')')[0])
            # print(command, self.pdata['team'], self.pdata['id'])
        return command

    def get_values_from_see(self, msg_part):
        """
        Get the values from the given object.

        Returns object type, distance, direction. If failed return 0, 0, 0

        msg_part - str: one part of a see message (one object)
        """

        try:
            object_type = msg_part.split(') ')[0].split('(')[1]
        except IndexError:
            return 0, 0, 0

        # get parameters of seen object
        parameters = msg_part.split(') ')[1]

        # return parameters if possible
        if len(parameters.split(' ')) >= 2:
            distance = parameters.split(' ')[0]
            direction = parameters.split(' ')[1]

            return object_type, distance, direction

        else:
            return 0, 0, 0

# TODO: (marker) disable in game mode
# Player('Team1')