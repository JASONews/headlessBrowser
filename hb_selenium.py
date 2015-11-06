from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.proxy import *
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
from functools import wraps
import sys
import time
import os
import signal
import errno
import json
import random


def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s : %0.5f s' % (f.func_name, (time2 - time1))
        return ret
    return wrap


class TimeoutError(Exception):
    pass


def timeout(seconds=300, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wraps(func)(wrapper)
    return decorator


def make_folder(path):
    try:
        command = "mkdir -p " + path
        if os.path.exists(path) is False:
            os.system(command)
    except Exception as e:
        pass


def save_screenshot(filename, path):
    #print filename, path
    make_folder(path)
    ss_path = path + '/' +str(filename) + ".png"
    driver.save_screenshot(ss_path)


def save_html(filename, path):
    make_folder(path)
    html_path = path + '/' +str(filename) + ".html"
    f = open(html_path, "w")
    #########IMPORTANT
    f.write(driver.page_source.encode("UTF-8"))
    f.close()


def open_virtual_display():
    display.start()


def close_virtual_display():
    display.stop()


@timing
def setup_profile(firebug=1, netexport=1, noscript=0):
    profile = webdriver.FirefoxProfile()
    profile.set_preference("app.update.enabled", False)
    # profile.set_preference("browser.cache.disk.enable", False)
    # profile.set_preference("browser.cache.memory.enable", False)
    # profile.set_preference("browser.cache.offline.enable", False)
    # profile.set_preference("network.http.use-cache", False)
    # profile.set_preference("browser.cache.disk_cache_ssl", False)
    if firebug == 1:
        profile.add_extension(capture_path + '/firebug-2.0.8.xpi')
        profile.set_preference("extensions.firebug.currentVersion", "2.0.8")
        profile.set_preference("extensions.firebug.allPagesActivation", "on")
        profile.set_preference("extensions.firebug.defaultPanelName", "net")
        profile.set_preference("extensions.firebug.net.enableSites", True)
        profile.set_preference("extensions.firebug.delayLoad", False)
        profile.set_preference("extensions.firebug.onByDefault", True)
        profile.set_preference("extensions.firebug.showFirstRunPage", False)
        profile.set_preference("extensions.firebug.net.defaultPersist", True)
    if netexport == 1:
        profile.add_extension(capture_path + '/netExport-0.9b7.xpi')
        profile.set_preference("extensions.firebug.DBG_NETEXPORT", True)
        profile.set_preference("extensions.firebug.netexport.alwaysEnableAutoExport", True)
        profile.set_preference("extensions.firebug.netexport.defaultLogDir", capture_path + "/har/"+url)
        profile.set_preference("extensions.firebug.netexport.includeResponseBodies", True)
    return profile


@timeout(seconds=20)
def wait_for_ready_state(time_, state):
    time.sleep(1)
    try:
        WebDriverWait(driver, int(time_)).until(lambda d: d.execute_script('return document.readyState') == 'interactive')
    except Exception as e:
        pass


@timeout(seconds=60)
def load_page(url, cookies=0):
    try:
        main_handle = driver.current_window_handle
        if cookies == 0:
            driver.delete_all_cookies()
            time.sleep(1)
        if "http" not in url.split("/")[0]:
            url = "http://" + url
        driver.get(url) # get the url. Web driver wil wait until the page is fully loaded
    except TimeoutException as te:
        print "Timeout Exception occurred while loading page: " + url
        print te
    try:
        WebDriverWait(driver, .5).until(EC.alert_is_present()) #web driver will wait for 0.5 second for alert
        alert = driver.switch_to_alert()
        alert.dismiss()
        windows = driver.window_handles
        if len(windows) > 1:
            for window in windows:
                if window != main_handle:
                    driver.switch_to_window(window)
                    driver.close() # it will close one tab
            driver.switch_to_window(main_handle)
        wait_for_ready_state(driver, 15, 'complete')
    except (TimeoutException, NoAlertPresentException):
        pass


def wrap_results():
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

def main():
    #status_fname = "status-experiment-"+ url
    try:
        load_page(url)
        f_name = url.split('/')[-1]
        make_folder(capture_path)
        save_html(f_name, capture_path + "/html/"+url)
        save_screenshot(f_name, capture_path + "/screenshots/"+url)
    except Exception as e:
	print "this is an exception"
        print e
    # f = open(status_fname, "w")
    # f.write("Experiment " + url + " is complete! \n")
    # f.flush()
    # f.close()
    driver.close()
    #wrap_results(capture_path+'/var/'+f_name+"*")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        str_err = "Usage: python hb_selenium.py url"
        print str_err
        raise SystemExit
    else:
        url = sys.argv[1]
        #display_ = 0
        capture_path = os.getcwd()
        #tag = 1
        display = Display(visible=False)
        #if display_ == 0:
        display.start()
        fd = capture_path + "/har/"+url
        make_folder(fd)
        profile = setup_profile(0,0,0) # set a new profile for firefox, you can use this profile to set preferences, home page etc.
        binary = FirefoxBinary('/usr/bin/firefox',sys.stdout)
        driver = webdriver.Firefox(firefox_profile=profile, firefox_binary=binary, timeout=900) # pass above created profile to be used in Firefox driver, and create a new Firefox Web driver object with that profile.
        driver.set_page_load_timeout(900) # set the page load element time to 60 secs.
        main()
        display.stop()
        #elem = driver.find_element_by_xpath("//*")
        #source_code = elem.get_attribute("outerHTML")
        #print source_code
        #element = driver.find_element_by_name('q')
        #print element
        #driver.quit()
        r = wrap_results()
        with open('./'+url.split('/')[-1]+'.json','w') as f:
            json.dump(r,f,indent=4)
	print 'hb end'
