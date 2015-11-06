from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.proxy import *
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
import foctor_core.foctor_core as fc
from functools import wraps
import sys
import time
import os
import signal
import errno
import json
import random


class HeadlessBrowser():

    def __init__(self):
        self.display = Display(visible=False)
        binary = FirefoxBinary(log_file=sys.stdout) # log_file for debbug
        profile = self.setup_profile()
        self.driver = webdriver.Firefox(firefox_profile=profile, firefox_binary=binary, timeout=60)
        self.driver.set_page_load_timeout(60)


    @fc.timing
    def setup_profile(self, firebug=True, netexport=True):
        """
        Setup the profile for firefox
        :param firebug: whether add firebug extension
        :param netexport: whether add netexport extension
        :return:
        """
        capture_path = os.getcwd()
        profile = webdriver.FirefoxProfile()
        profile.set_preference("app.update.enabled", False)
        if firebug:
            profile.add_extension(capture_path + '/firebug-2.0.8.xpi')
            profile.set_preference("extensions.firebug.currentVersion", "2.0.8")
            profile.set_preference("extensions.firebug.allPagesActivation", "on")
            profile.set_preference("extensions.firebug.defaultPanelName", "net")
            profile.set_preference("extensions.firebug.net.enableSites", True)
            profile.set_preference("extensions.firebug.delayLoad", False)
            profile.set_preference("extensions.firebug.onByDefault", True)
            profile.set_preference("extensions.firebug.showFirstRunPage", False)
            profile.set_preference("extensions.firebug.net.defaultPersist", True)
        if netexport:
            profile.add_extension(capture_path + '/netExport-0.9b7.xpi')
            profile.set_preference("extensions.firebug.DBG_NETEXPORT", True)
            profile.set_preference("extensions.firebug.netexport.alwaysEnableAutoExport", True)
            profile.set_preference("extensions.firebug.netexport.defaultLogDir", capture_path + "/har/")
            profile.set_preference("extensions.firebug.netexport.includeResponseBodies", True)
        return profile


    def open_virtual_display(self):
        self.display.start()


    def close_virtual_display(self):
        self.display.stop()


    def wrap_results(self, fd):
        """
        Wrap returned http response into a well formatted dict
        :param fd: the directory in which har files lie
        :return: Dict
        """
        for fn in os.listdir(fd):
            results = {}
            if fn.endswith(".har"):
                with open(fd+'/'+fn) as f:
                    raw_data = json.load(f)['log']['entries']
                    results = [{} for i in range(0, len(raw_data))]
                    for i in range(0, len(results)):
                        results[i]['request'] = {}
                        results[i]['request']['method'] = raw_data[i]['request']['method']
                        results[i]['request']['headers'] = raw_data[i]['request']['headers']
                        results[i]['response'] = {}
                        results[i]['response']['status'] = raw_data[i]['response']['status']
                        results[i]['response']['reason'] = raw_data[i]['response']['statusText']
                        results[i]['response']['headers'] = raw_data[i]['response']['headers']
                        results[i]['response']['redirect'] = raw_data[i]['response']['redirectURL']
                        results[i]['response']['body'] = raw_data[i]['response']['content']

                break
        return results

    def get(self, host, path="/", url=None):
        """
        Send get request to a url and wrap the results
        :param host:
        :param path:
        :return:
        """
        if url is None:
            url = host+path
        try:
            capture_path = os.getcwd()


            # SAVE THE HAR FILE UNDER THE FOLDER NAMED BY ITS URL
            self.driver.firefox_profile.set_preference("extensions.firebug.netexport.defaultLogDir", capture_path + "/har/"+url)

            fc.load_page(self.driver, url)

            f_name = url.split('/')[-1]
            fc.make_folder(capture_path+"/har")
            fc.save_html(f_name, capture_path + "/html/"+url+"/")
            fc.save_screenshot(f_name, capture_path + "/screenshots/"+url+"/")

            har_file_path = capture_path + "/har/" + url
            return self.wrap_results(har_file_path)
        except Exception as e:
            print e
        self.driver.close()

    def get_batch(self, input_list, delay_time=.5, max_threads= 100):
        """

        :param input_list:
        :param delay_time:
        :param max_threads:
        :return:
        """
        raise NotImplementedError()
        results = {}