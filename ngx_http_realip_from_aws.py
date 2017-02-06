#!/usr/bin/env python
import yaml, requests, json, sys, os, filecmp, subprocess, logging, time
from os import path
from logging.handlers import RotatingFileHandler
from logging import StreamHandler

class Config(object):
    def __init__(self, cfgfile):
        if path.exists(cfgfile):
            try:
                with open(cfgfile, 'r') as cfgfile:
                    self.config = yaml.load(cfgfile)
            except Exception as e:
                #Gotta Catch'em All
                print("Failed to load config file. Error: '{0}' occured.".format(e.args))

    def get_config(self):
        return self.config

class Log(object):
    def __init__(self, config):
        self.config = config.get_config()

        self.logger=logging.getLogger(self.config['log_name'])
        self._remove_handlers()
        self._add_handler()
        self.logger.setLevel(self.config['log_level'])

        if not os.path.exists(self.config['log_dir']):
            os.makedirs(self.config['log_dir'])

    def _remove_handlers(self):
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)

    def _add_handler(self):
        try:
            handler=RotatingFileHandler(
                '%s/%s' % (self.config['log_dir'], self.config['log_name']),
                maxBytes=10485760,
                backupCount=3
            )
            formatter=logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        except IOError:
            self.logger.addHandler(StreamHandler(sys.stderr))

class RealIP(object):
    def __init__(self, config):
        self.config = config.get_config()
        self.logger = logging.getLogger(self.config['log_name'])

    def write_realip_file(self, ip_ranges, fpath):
        fo = open(fpath, "wb")
        for ip_range in ip_ranges:
            l = 'set_real_ip_from {0};\n'.format(ip_range)
            try:
                fo.write(str.encode(l))
            except Exception as e:
                #Gotta Catch'em All
                self.logger.error("'{0}' occured. Arguments {1}.".format(e.message, e.args))
        fo.close()
        self.logger.info('Wrote {0} ip ranges to {1}'.format(len(ip_ranges), fpath))

    def run(self):
        self.logger.info('Script started - Checking for changes every {0} minutes'.format(self.config['update_interval']))
        ranges = []
        r = 0

        #Load ranges from json and append to static ranges
        self.logger.info('Fetching ip range from Amazon')
        try:
            r = requests.get(self.config['ip_ranges_json'])
            d = r.text
            l = json.loads(d)

            self.logger.debug('JSON Response from AWS:\n {0}'.format(d))

            r_status = r.status_code

            for ip_range in [x['ip_prefix'] for x in l['prefixes'] if x['service']==self.config['service'] ]:
                ranges.append(ip_range)
        except Exception as e:
            # Gotta Catch'em All
            self.logger.error("Reading json-file. Error: '{0}' occured.".format(e.args))
        # Count ranges
        ranges_length = len(ranges)

        # Make sure that we have more than expected ranges, http ok and json content.
        if not(ranges_length < self.config['min_expected_ranges']):
            if r.status_code == requests.codes.ok:
                if r.headers['Content-Type'] == 'application/json':
                    nginx_cfg = self.config['nginx_conf_path'] + self.config['nginx_conf_name']
                    nginx_cache = self.config['nginx_conf_cache_name']

                    # Always create range cache
                    self.write_realip_file(ranges, nginx_cache)

                    # Write cfg file if it doesn't exist
                    if not os.path.isfile(nginx_cfg):
                        self.write_realip_file(ranges, nginx_cfg)
                    else:
                        # If file exists, only write if range has changed
                        if not(filecmp.cmp(nginx_cfg, nginx_cache)):
                            self.logger.info('IP range change detected!')
                            self.write_realip_file(ranges, nginx_cfg)
                            # Reload nginx
                            try:
                                subprocess.call('/opt/ngx_http_realip_from_aws/sh/reload_nginx.sh')
                            except Exception as e:
                                # Gotta Catch'em All
                                self.logger.error("Reloading nginx. Error: '{0}' occured.".format(e.args))
                        else:
                            self.logger.info('No changes to apply')

        time.sleep(self.config['update_interval']*60)

def main():
    config = Config('config.yml')
    Log(config)
    while True:
        RealIP(config).run()

if __name__ == '__main__':
    main()
