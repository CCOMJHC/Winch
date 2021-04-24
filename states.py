from abc import ABCMeta, abstractmethod
import os
import socket
from time import sleep
from time import time
import threading
try:
    import RPi.GPIO as GPIO
except:
    pass


class State(metaclass=ABCMeta):
    """State base class"""

    def __init__(self, name):
        self.__name = name

    def __str__(self):
        return self.__name

    def get_name(self):
        """
        Get the name of the current state
        :return: String
        """
        return self.__name

    @abstractmethod
    def on_entry_behavior(self, winch):
        """
        Entry behavior of the state
        :param winch: Context
        :return:
        """
        pass

    @abstractmethod
    def on_exit_behavior(self, winch):
        """
        Exits behavior of the state
        :param winch: Context
        :return:
        """
        pass


class InitState(State):
    def on_entry_behavior(self, winch):
        """
        Set the default parameters of the winch
        :param winch: Context
        :return:
        """
        ## Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        
        ## Name the pins for control and sensing.
        winch.slack_pin = 6
        winch.dock_pin = 17
        winch.at_line_end_pin = 12
        winch.up_pin = 23
        winch.down_pin = 24
        winch.rotations_pin = 21
        
        ## Setup motor control
        # Set each pin as an output and make it low:
        GPIO.setup(winch.up_pin, GPIO.OUT)
        GPIO.output(winch.up_pin, GPIO.LOW)
        GPIO.setup(winch.down_pin, GPIO.OUT)
        GPIO.output(winch.down_pin, GPIO.LOW)
            
        ## Setup slack sensor
        GPIO.setup(winch.slack_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(winch.slack_pin, GPIO.BOTH)
        
        ## Setup Docked and End of Line Sensors:
        # FIX: Need to add callbacks to these event_detect statements.
        # so they are registered even when not operating winch. 
        GPIO.setup(winch.dock_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(winch.dock_pin, GPIO.BOTH)
        GPIO.setup(winch.at_end_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(winch.at_line_end_pin, GPIO.BOTH)
        
        ## Setup rotations Counter
        GPIO.setup(winch.rotations_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.add_event_detect(winch.rotations_pin, GPIO.FALLING,
                              callback = winch.gotWheelTurn,
                              bouncetime = 100)
        
        ## Read counter calibration data
        
        with file(self.cal_file) as F:
            
            winch.cal_data['rotations'] = []
            winch.cal_data['meters'] = []
            while True:
                try:
                    rot, m = F.readline().split()
                    winch.cal_data['rotations'].append(rot)
                    winch.cal_data['meters'].append(m)
                except:
                    print("Finished reading cal data.")
                    print("Read %d values." % len(winch.cal_data['rotations']))
                    break
        
        #
        #
         #winch.payout_rate = int(input("Payout rate: "))

        command_thread = threading.Thread(target=winch.receive_commands)
        command_thread.start()
        
        winch.queue_command({"from": "INIT", "to": "STDBY"})
        winch.execute_state_stack()
        

    def on_exit_behavior(self, winch):
        pass

    def __init__(self, name):
        State.__init__(self, name)


class StdbyState(State):

    def on_entry_behavior(self, winch):
        """
        Standby waiting for commands
        :param winch: Context
        :return:
        """
        
        while winch.command is None:
            pass
        winch.queue_command({"from": "STDBY", "to": winch.command})
        winch.execute_state_stack()

    def on_exit_behavior(self, winch):
        pass

    def __init__(self, name):
        State.__init__(self, name)


class CastState(State):

    def on_entry_behavior(self, winch):
        """
        Automatically downcast and upcast to a specific depth
        :param winch: Context
        :return:
        """
        winch.target_depth = int(input("Enter depth: "))
        winch.queue_command({"from": "CAST", "to": "DOWNCAST"})
        winch.queue_command({"from": "DOWNCAST", "to": "UPCAST"})
        winch.queue_command({"from": "UPCAST", "to": "READDATA"})
        winch.execute_state_stack()

    def on_exit_behavior(self, winch):
        pass

    def __init__(self, name):
        State.__init__(self, name)


class ManualWinchOutState(State):
    def on_entry_behavior(self, winch):
        """
        Manually winch out n meters
        :param winch: Context
        :return:
        """
            
        while winch.command == "MANOUT":
            if winch.has_slack() or winch.is_out_of_line(): #slack
                winch.stop()
            else: winch.down()
        winch.stop()

    def on_exit_behavior(self, winch):
        pass

    def __init__(self, name):
        State.__init__(self, name)


class ManualWinchInState(State):
    def on_entry_behavior(self, winch):
        """
        Manually winch in n meters
        :param winch: Context
        :return:
        """
        while winch.command == "MANIN":
            if winch.has_slack() or winch.is_docked(): #slack
               winch.stop()
            else: winch.up()
        winch.stop()
        
    def on_exit_behavior(self, winch):
        pass

    def __init__(self, name):
        State.__init__(self, name)


class DownCastState(State):
    def on_entry_behavior(self, winch):
        """
        Downcast while less than target
        :param winch:
        :return:
        """
        winch.down()
        while winch.receive_command() == "MANOUT":
            pass
        winch.stop()

    def on_exit_behavior(self, winch):
        pass

    def __init__(self, name):
        State.__init__(self, name)


class UpCastState(State):
    def on_entry_behavior(self, winch):
        """
        Upcast while greater than target
        :param winch: Context
        :return:
        """
        while winch.depth > 0:
            winch.up()

    def on_exit_behavior(self, winch):
        pass

    def __init__(self, name):
        State.__init__(self, name)


class ReadDataState(State):
    def on_entry_behavior(self, winch):
        """
        Read CTD info from winch
        :param winch: Context
        :return:
        """
        if winch.is_docked():
            winch.error("Winch not docked, cannot read data")

        print("C:", winch.conductivity, "T:", winch.temp, "D:", winch.depth)

    def on_exit_behavior(self, winch):
        pass

    def __init__(self, name):
        State.__init__(self, name)


class ErrorState(State):
    def on_entry_behavior(self, winch):
        """
        Handle errors that occur
        :param winch: Context
        :return:
        """
        winch.state_sequence = []
        print("ERROR:", winch.error_message)
        winch.error_message = ""
        winch.queue_command({"from": "ERROR", "to": "STDBY"})
        winch.execute_state_stack()

    def on_exit_behavior(self, winch):
        pass

    def __init__(self, name):
        State.__init__(self, name)


class HelpState(State):

    def on_entry_behavior(self, winch):
        """
        Print the available state commands
        :param winch: Context
        :return:
        """
        winch.print_states()

    def on_exit_behavior(self, winch):
        pass

    def __init__(self, name):
        State.__init__(self, name)
