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
import threading


class HeadlessBrowser:

    def __init__(self):
        self.display = Display(visible=False)
        self.binary = None
        self.profile = None
        self.driver = None


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
        results = {}
        for fn in os.listdir(fd):
            if fn.endswith(".har"):
                with open(fd+'/'+fn) as f:
                    raw_data = json.load(f)['log']['entries']
                    results = [{} for i in range(0, len(raw_data))]
                    for i in range(0, len(results)):

                        results[i]['request'] = {}
                        results[i]['request']['method'] = raw_data[i]['request']['method']
                        headers = {}
                        for header in raw_data[i]['request']['headers']:
                            headers[header['name']] = header['value']
                        results[i]['request']['headers'] = headers

                        results[i]['response'] = {}
                        results[i]['response']['status'] = raw_data[i]['response']['status']
                        results[i]['response']['reason'] = raw_data[i]['response']['statusText']
                        headers = {}
                        for header in raw_data[i]['response']['headers']:
                            headers[header['name']] = header['value']
                        results[i]['response']['headers'] = headers
                        results[i]['response']['redirect'] = raw_data[i]['response']['redirectURL']
                        results[i]['response']['body'] = raw_data[i]['response']['content']

                break
        return results



    def get(self, host, path="", ssl=False, external=None):
        """
        Send get request to a url and wrap the results
        :param host:
        :param path:
        :return:
        """
        theme = "https" if ssl else "http"
        url = host+path
        http_url = theme+"://"+url

        result = {}
        try:
            capture_path = os.getcwd()

            # SAVE THE HAR FILE UNDER THE FOLDER NAMED BY ITS URL
            profile = self.setup_profile()
            profile.set_preference("extensions.firebug.netexport.defaultLogDir", capture_path + "/har/"+url)
            profile.update_preferences()
    
            if self.binary is None:
                self.binary = FirefoxBinary(log_file=sys.stdout) # log_file for debug

            driver = webdriver.Firefox(firefox_profile=profile, firefox_binary=self.binary, timeout=60)
            driver.set_page_load_timeout(60)
            self.driver = driver
            fc.load_page(driver, http_url)
            self.wait_for_ready_state(time_=5, state="interactive")

            if url[-1] == "/":
                f_name = url.split('/')[-2]
            else:
                f_name = url.split('/')[-1]

            fc.make_folder(capture_path+"/har/"+url)
            fc.save_html(driver, f_name, capture_path + "/html/"+url+"/")
            fc.save_screenshot(driver, f_name, capture_path + "/screenshots/"+url+"/")


            har_file_path = capture_path + "/har/" + url
            print har_file_path
            result = self.wrap_results(har_file_path)

            if external is not None:
                external[http_url] = result

       	    driver.close()
        except Exception as e:
            result['error'] = e.message
            print e

        return result



    def get_batch(self, input_list, delay_time=.5, max_threads= 100):
        """

        :param input_list:
        :param delay_time:
        :param max_threads:
        :return:
        """

        results = {}

        ssl = False
        path = "/"
        host = None

        threads = []
        threads_error = False
        thread_wait_timeout = 200

        for row in input_list:

            if type(row) is 'dict':
                if "host" not in row:
                    continue
                host = row['host']

                if "path" in row:
                    path = row['path']
                if "ssl" in row:
                    ssl = row['ssl']
            else:
                host = row

            self.get(host, path, ssl, external=results)

        #     wait_time = 0
        #
        #     while threading.activeCount() > max_threads:
        #         time.sleep(1)
        #         wait_time += 1
        #         if wait_time >= thread_wait_timeout:
        #             threads_error = True
        #             break
        #
        #     if threads_error:
        #         results['error'] = "Threads took too long to finish."
        #         break
        #
        #     time.sleep(delay_time)
        #
        #     thread = threading.Thread(target=self.get,args=(host, path, ssl, results))
        #
        #     thread.setDaemon(1)
        #     thread.start()
        #     threads.append(thread)
        #
        # for thread in threads:
        #     thread.join(thread_wait_timeout)

        return results


    def quit(self):
        """
        close webdriver and clean tmp files
        :return:
		"""
        if self.driver is not None:
            self.driver.quit()


    def run(self, url=None, input_list=None):
        """
        run the headless browser with given input
        if url given, the proc will only run hlb with given url and ignore input_list.
        :param url:
        :param input_list:
        :return:
        """
        if not url and not input_list:
            print 'no inputs'
            return {"error" : "no inputs"}
        results = {}

        self.open_virtual_display()

        if url:
            host = url.split["/"][0]
            path = url.split["/"][1:]
            results[url] = self.get(host,path)

        else:
            results_list = self.get_batch(input_list)
            for key, value in results_list.iteritems():
                results[key] = value

        self.quit()
        self.close_virtual_display()

        with open("./hlb_results.json", "w") as f:
            json.dump(results, f, indent=4)

        print "hlb test finished"
        return results


    @fc.timeout(seconds=20)
    def wait_for_ready_state(self, time_, state):
        time.sleep(1)
        try:
            WebDriverWait(self.driver, int(time_)).until(lambda d: d.execute_script('return document.readyState') == state)
        except Exception as e:
            print e
            pass
