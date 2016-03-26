#!/usr/bin/env python
#
# antcontrol.py
#
# Controller API for the Antenna Switch application
# 
# Copyright (C) 2015 by G3UKB Bob Cowdery
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#    
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#    
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#    
#  The author can be reached by email at:   
#     bob@bobcowdery.plus.com
#

# System imports
import socket
import threading
import traceback

# Application imports
from common import *

"""
Controller API
"""
class AntControl :
    
    def __init__(self, network_params, relay_state, callback):
        """
        Constructor
        
        Arguments:
        
            network_params   --  [ip, port] address of Arduino
            relay_state      --  initial relay state
            callback         --  status and progress callback
        """
        
        if len(network_params) == 0 or network_params[0]== None or network_params[1]== None:
            # Not configured yet
            self.__ip = None
            self.__port = None
            self.__ready = False
        else:
            self.__ip = network_params[0]
            self.__port = int(network_params[1])
            self.__ready = True
               
        # Callback here with progress, SWR, completion etc
        self.__callback = callback
        # Current state of relays
        self.__relay_state = relay_state
        
        if self.__ready:
            # Create UDP socket
            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Set the relays according to the state
            for relay_id, state in self.__relay_state.items():
                self.set_relay(relay_id, state)

    def resetNetworkParams(self, ip, port):
        """
        Parameters (may) have changed
        
        Arguments:
        
            ip          --  IP address of Arduino
            port        --  port address for Arduino
        """
        
        self.__ip = ip
        self.__port = int(port)
        self.__ready = True
        # Set the relays according to the state
        for relay_id, state in self.__relay_state.items():
            self.set_relay(relay_id, state)
    
    # API =============================================================================================================
    def set_relay(self, relay_id, switch_to):
        """
        Parameters (may) have changed
        
        Arguments:
        
            relay_id    --  1-6
            switch_to   --  RELAY_ON|RELAY_OFF
        """
        
        if not self.__ready:
            self.__callback('failure: no network params!')
            return
        if switch_to == RELAY_ON:
            self.__send(str(relay_id) + 'e')
        else:
            self.__send(str(relay_id) + 'd')
        self.__doReceive()
    
    def reset_relays(self, ):
        """ Set all relays de-energised """
        
        if self.__ready:
            for relay_id in range(1,7):
                self.set_relay(relay_id, RELAY_OFF)
            
    
    # Helpers =========================================================================================================    
    def __send(self, command):
        
        self.__sock.sendto(bytes(command, "utf-8"), (self.__ip, self.__port))
        
    def __doReceive(self, wait=False):
        
        t = threading.Thread(target=receive, args=(self.__sock, self.__callback))
        t.start()
        if wait:
            t.join()

# Receive loop ========================================================================================================        
# Runs on separate thread as calls are from within a UI event proc so need to detach the long running part and
# also allow the UI to continue to display status changes.
def receive(sock, callback):
        
    try:
        callback('Communicating with controller...')
        sock.settimeout(5)
        while(1):
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            asciidata = data.decode(encoding='UTF-8')
            callback(asciidata)
            if 'success' in asciidata or 'failure' in asciidata :
                # All done so exit thread
                break
    except socket.timeout:
        # Server didn't respond
        callback('failure: timeout on read!')
    except Exception as e:
        # Something went wrong
        callback('failure: {0}'.format(e))
        
