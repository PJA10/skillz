# coding=utf-8

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
import math
import itertools as it


def main():
    start_time = time.time()
    large_groups_dic = {u"ישיבת צביה אשקלון 1": [0, 2],
                        u"הכפר הירוק 1": [0, 3],
                        u"רונסון 1": [0, 20],
                        u"בני עקיבא 3": [0, 13],
                        u"נזירות סנט גוזף 1": [0, 42],
                        u"אסף רמו 1": [0, 29],
                        u"רוטברג 6": [0, 44],
                        u"שוהם 1": [0, 15],
                        u"עמי אסף 1": [0, 6],
                        u"רוטברג 2": [0, 16],
                        u"אלתרמן 1": [0, 48],
                        u"חיל האויר 1": [0, 8],
                        u"טכנאים והנדסאים 1": [0, 43],
                        u"דה שליט 6": [0, 39],
                        u"הרצליה 2": [0, 14],
                        u"שיבת חורב 1": [0, 9],
                        u"רוטברג 4": [0, 17],
                        u"סנט גוזף 2": [0, 5],
                        u"דה שליט 2": [0, 12],
                        u"דה שליט 4": [0, 7],
                        u"רביבים 1": [0, 30],
                        u"אורנית 1": [0, 47],
                        u"רעות-תיכ 1": [0, 50],
                        u"אוסטרובסקי 2": [0, 41],
                        u"אבין 3": [0, 46],
                        u"חקלאי נהלל 4": [0, 1],
                        u"אחד העם 1": [0, 11],
                        u"צביה אשקלון 3": [0, 19],
                        u"רמת השרון 2": [0, 23],
                        u"גוש דן 1": [0, 24],
                        u"אלרסאלה 1": [0, 26],
                        u"עמי אסף 3": [0, 27],
                        u"עודד רא 2": [0, 31],
                        u"אהל שם 4": [0, 32],
                        u"שעלי תורה 2": [0, 22],
                        u"מקיף באר טוביה 3": [0, 33],
                        u"עמי שמר 1": [0, 34],
                        u"קיף גוונים 1": [0, 35],
                        u"שעלי תורה 4": [0, 36],
                        u"וייס מיתרי 1": [0, 37],
                        u"פארק המדע 3": [0, 38],
                        u"עש קררי 2": [0, 40],
                        u"אבין 2": [0, 28]}

    for i in range(15):
        groups_dic = {}
        for group in large_groups_dic:
            if i*10 < large_groups_dic[group][1] <= (i+1) * 10:
                groups_dic[group] = large_groups_dic[group]
        if not groups_dic:
            continue
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}
        driver = webdriver.Chrome(executable_path='.\chromedriver\chromedriver.exe', desired_capabilities=d)
        driver.get("https://piratez.skillz-edu.org/home/")

        email = driver.find_element_by_id("id_email")
        email.send_keys("alon.w.10@gmail.com")

        password = driver.find_element_by_id("id_password")
        password.send_keys("alon1234")

        submit = driver.find_element_by_id("submit_login")
        # print "got submit"
        # submit.set_attribute('style', 'width: 10%')
        # print "changed submit width"
        submit.click()
        # print "clicked submit"

        tournament = driver.find_element_by_id("tournament_button_1")
        tournament.click()

        # print "preesed tournament"
        for group in groups_dic:
            first_window = driver.window_handles[0]
            driver.switch_to.window(first_window)
            race = driver.find_element_by_xpath('//*[@id="menu_button_try_to_win"]')
            race.send_keys(Keys.CONTROL + Keys.RETURN)
            #driver.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 't')

            time.sleep(1)
            driver.switch_to.window(driver.window_handles[-1])

            #driver.get("https://piratez.skillz-edu.org/group_dashboard/try_to_win/group/40956/select")
            driver.page_source.encode('utf-8')

            name = driver.find_element_by_class_name("name")
            name.clear()
            name.send_keys(group)

            team_link = driver.find_element_by_class_name("dropdown-item")
            team_link.click()

            run_button = driver.find_element_by_class_name("play")
            run_button.click()
            groups_dic[group][0] = driver.window_handles[-1]

        for group in groups_dic:
            driver.switch_to.window(groups_dic[group][0])
            play_link = driver.find_element_by_id("play-link")

            finished = False
            while not finished:
                for entry in driver.get_log('browser'):
                    # print entry
                    if "status: DONE" in entry['message']:
                        finished = True

            play_link.click()

            time.sleep(0.1)
            driver.switch_to.window(groups_dic[group][0])
            groups_dic[group][0] = driver.window_handles[driver.window_handles.index(groups_dic[group][0])+1]
            driver.close()
            time.sleep(0.1)

            time.sleep(1)

        for window, group in zip(driver.window_handles[1:], groups_dic):
            driver.switch_to.window(window)
            time.sleep(1)
            sound = driver.find_element_by_xpath('//*[@id="right-settings"]/volume-button/i')
            sound.click()
            turn = driver.find_element_by_xpath('//*[@id="turn"]')
            while True:
                if turn.text != "Turn 0/":
                    break

            time.sleep(3)
            next_turn = driver.find_element_by_xpath('//*[@id="left-settings"]/i[3]')
            for i in range(2):
                next_turn.click()
            time.sleep(2)

            driver.find_element_by_xpath('/html/body').send_keys(Keys.END)


            team_one_name = driver.find_element_by_xpath('//*[@id="score-ui"]/player-ui[1]/div/div[2]/div[1]')
            team_one_score = driver.find_element_by_xpath('//*[@id="score-ui"]/player-ui[1]/div/div[2]/div[2]/div/span')
            team_two_name = driver.find_element_by_xpath('//*[@id="score-ui"]/player-ui[2]/div/div[2]/div[1]')
            team_two_score = driver.find_element_by_xpath('//*[@id="score-ui"]/player-ui[2]/div/div[2]/div[2]/div/span')
            print ("------------------")
            print ("against %s" % groups_dic[group][1])
            print ("team_one_score: %s, team_two_score: %s" % (team_one_score.text, team_two_score.text))
            if int(team_one_score.text[:-4]) > int(team_two_score.text[:-4]):
                # print "h"

                if u"שפיה" in team_one_name.text:
                    print ("we won")
                else:
                    print ("we lost")
            elif int(team_two_score.text[:-4]) > int(team_one_score.text[:-4]):
                if u"שפיה" in team_two_name.text:
                    print ("we won")
                else:
                    print ("we lost")
            else:
                print ("dont know")

        driver.quit()

    print ("bot time: %s" % str(time.time()-start_time))
    time.sleep(160)

main()
