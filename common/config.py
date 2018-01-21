# -*- coding: utf-8 -*-
"""
调取配置文件和屏幕分辨率的代码
"""
import os
import sys
import json
import re

class Config:
    def get_config(self, key_name=''):
        config_file = "{path}/config/config.json".format(
            path=sys.path[0]
        )
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config[key_name]
