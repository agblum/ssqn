# Created by alex at 15.06.23

import os
import sys
import configparser
import logging


class Config:

    def __init__(self, config_file):
        self.config_file = config_file
        self.errors = set()
        self.__readConfig()

    def __readConfig(self):
        config = configparser.ConfigParser(strict=False, interpolation=None)
        if not os.path.exists(self.config_file):
            logging.error("Config file '{}' does not exists.".format(self.config_file))
            exit(1)
        config.read(self.config_file)

        self.server = config['General']['server']
        self.authentication_endpoint = self.server + config['General']['authentication_endpoint']

        self.sewage_samples_endpoint = self.server + config['General']['sewage_samples_endpoint']
        self.sewage_locations_endpoint = self.server + config['General']['sewage_locations_endpoint']


        self.bay_voc_username = config['BayVOC']['user']
        self.bay_voc_password = config['BayVOC']['password']

        self.mail_host = config['Mail']['host']
        self.mail_port = config['Mail']['port']
        self.mail_user = config['Mail']['user']
        self.mail_password = config['Mail']['password']

